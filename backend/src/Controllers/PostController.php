<?php
namespace App\Controllers;

use App\Config\Database;
use App\Middleware\Auth;
use App\Services\AiClient;
use App\Services\Response;
use PDO;

final class PostController
{
    public static function index(): never
    {
        $pdo = Database::connection();
        $where = ['p.status <> "CLOSED"'];
        $params = [];
        foreach (['post_type','category_id','color','brand'] as $f) {
            if (isset($_GET[$f]) && $_GET[$f] !== '') {
                $where[] = "p.{$f} = ?";
                $params[] = $_GET[$f];
            }
        }
        if (!empty($_GET['q'])) {
            $where[] = '(p.title LIKE ? OR p.description LIKE ? OR p.location LIKE ?)';
            $q = '%' . $_GET['q'] . '%';
            array_push($params, $q, $q, $q);
        }
        $sql = 'SELECT p.*, c.name category_name, u.full_name owner_name, (SELECT image_path FROM images i WHERE i.post_id=p.id ORDER BY is_primary DESC,id LIMIT 1) primary_image FROM posts p JOIN categories c ON c.id=p.category_id JOIN users u ON u.id=p.user_id WHERE '.implode(' AND ',$where).' ORDER BY p.created_at DESC LIMIT 100';
        $stmt = $pdo->prepare($sql); $stmt->execute($params);
        Response::json($stmt->fetchAll());
    }

    public static function show(int $id): never
    {
        $pdo = Database::connection();
        $stmt = $pdo->prepare('SELECT p.*,c.name category_name,u.full_name owner_name FROM posts p JOIN categories c ON c.id=p.category_id JOIN users u ON u.id=p.user_id WHERE p.id=?');
        $stmt->execute([$id]); $post = $stmt->fetch();
        if (!$post) Response::json(null,404,'Không tìm thấy bài đăng');
        $img = $pdo->prepare('SELECT id,image_path,is_primary FROM images WHERE post_id=? ORDER BY is_primary DESC,id');
        $img->execute([$id]); $post['images']=$img->fetchAll();
        Response::json($post);
    }

    public static function create(): never
    {
        $user = Auth::user();
        $b = json_decode(file_get_contents('php://input'), true) ?: [];
        foreach(['category_id','post_type','title','description','location','event_date'] as $f) if(empty($b[$f])) Response::json(null,422,"Thiếu trường {$f}");
        if(!in_array($b['post_type'],['LOST','FOUND'],true)) Response::json(null,422,'post_type phải là LOST hoặc FOUND');

        $pdo=Database::connection();
        $stmt=$pdo->prepare('INSERT INTO posts(user_id,category_id,post_type,title,description,color,brand,location,event_date,contact,reward,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,NOW())');
        $stmt->execute([(int)$user->sub,(int)$b['category_id'],$b['post_type'],trim($b['title']),trim($b['description']),$b['color']??null,$b['brand']??null,trim($b['location']),$b['event_date'],$b['contact']??null,$b['reward']??0,'OPEN']);
        $id=(int)$pdo->lastInsertId();
        self::runMatching($id);
        Response::json(['id'=>$id],201,'Tạo bài đăng thành công');
    }

    public static function uploadImage(int $id): never
    {
        $user=Auth::user(); $pdo=Database::connection();
        $stmt=$pdo->prepare('SELECT user_id FROM posts WHERE id=?'); $stmt->execute([$id]); $post=$stmt->fetch();
        if(!$post) Response::json(null,404,'Không tìm thấy bài đăng');
        if((int)$post['user_id']!==(int)$user->sub && ($user->role??'')!=='ADMIN') Response::json(null,403,'Không có quyền sửa bài đăng này');
        if(empty($_FILES['image']['tmp_name'])) Response::json(null,422,'Thiếu file image');
        $mime=mime_content_type($_FILES['image']['tmp_name']);
        $ext=['image/jpeg'=>'jpg','image/png'=>'png','image/webp'=>'webp'][$mime]??null;
        if(!$ext) Response::json(null,422,'Chỉ hỗ trợ JPG, PNG, WEBP');
        if($_FILES['image']['size']>5*1024*1024) Response::json(null,422,'Ảnh tối đa 5MB');
        $dir=getenv('UPLOAD_DIR')?:'/var/www/html/uploads'; if(!is_dir($dir)) mkdir($dir,0775,true);
        $name=bin2hex(random_bytes(16)).'.'.$ext; $path=$dir.'/'.$name;
        if(!move_uploaded_file($_FILES['image']['tmp_name'],$path)) Response::json(null,500,'Không lưu được ảnh');
        $count=$pdo->prepare('SELECT COUNT(*) FROM images WHERE post_id=?');$count->execute([$id]);$primary=((int)$count->fetchColumn()===0)?1:0;
        $ins=$pdo->prepare('INSERT INTO images(post_id,image_path,is_primary) VALUES(?,?,?)');$ins->execute([$id,'/uploads/'.$name,$primary]);
        Response::json(['id'=>(int)$pdo->lastInsertId(),'path'=>'/uploads/'.$name],201,'Tải ảnh thành công');
    }

    public static function myPosts(): never
    {
        $user=Auth::user();$stmt=Database::connection()->prepare('SELECT * FROM posts WHERE user_id=? ORDER BY created_at DESC');$stmt->execute([(int)$user->sub]);Response::json($stmt->fetchAll());
    }

    public static function close(int $id): never
    {
        $user=Auth::user();$pdo=Database::connection();$stmt=$pdo->prepare('UPDATE posts SET status="CLOSED" WHERE id=? AND (user_id=? OR ?="ADMIN")');$stmt->execute([$id,(int)$user->sub,$user->role??'']);
        if($stmt->rowCount()===0) Response::json(null,404,'Không tìm thấy bài đăng hoặc không có quyền');
        Response::json(['id'=>$id],200,'Đã đóng bài đăng');
    }

    private static function runMatching(int $postId): void
    {
        $pdo=Database::connection();
        $s=$pdo->prepare('SELECT * FROM posts WHERE id=?');$s->execute([$postId]);$post=$s->fetch(); if(!$post)return;
        $opposite=$post['post_type']==='LOST'?'FOUND':'LOST';
        $q=$pdo->prepare('SELECT * FROM posts WHERE post_type=? AND status="OPEN" AND category_id=? AND id<>? ORDER BY created_at DESC LIMIT 50');$q->execute([$opposite,$post['category_id'],$postId]);
        $threshold=(float)(getenv('AI_MATCH_THRESHOLD')?:0.72);
        foreach($q->fetchAll(PDO::FETCH_ASSOC) as $candidate){
            $score=AiClient::similarity($post,$candidate);
            if($score<$threshold) continue;
            $lost=$post['post_type']==='LOST'?$post:$candidate; $found=$post['post_type']==='FOUND'?$post:$candidate;
            $ins=$pdo->prepare('INSERT INTO matches(lost_post_id,found_post_id,similarity_score,ai_model,status,created_at) VALUES(?,?,?,?,"PENDING",NOW()) ON DUPLICATE KEY UPDATE similarity_score=VALUES(similarity_score), ai_model=VALUES(ai_model)');
            $ins->execute([$lost['id'],$found['id'],$score,'hybrid-text-v1']);
            foreach(array_unique([(int)$lost['user_id'],(int)$found['user_id']]) as $uid){
                $n=$pdo->prepare('INSERT INTO notifications(user_id,title,content,is_read,created_at) VALUES(?,?,?,0,NOW())');
                $n->execute([$uid,'Có đồ vật tương đồng',sprintf('Hệ thống phát hiện một bài đăng có độ tương đồng %.1f%%.', $score*100)]);
            }
        }
    }
}
