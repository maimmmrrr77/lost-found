<?php
namespace App\Controllers;

use App\Config\Database;
use App\Middleware\Auth;
use App\Services\Response;

final class MatchController
{
    public static function mine(): never
    {
        $u=Auth::user();
        $sql='SELECT m.*, lp.title lost_title, lp.user_id lost_user_id, fp.title found_title FROM matches m JOIN posts lp ON lp.id=m.lost_post_id JOIN posts fp ON fp.id=m.found_post_id WHERE lp.user_id=? OR fp.user_id=? ORDER BY m.similarity_score DESC,m.created_at DESC';
        $s=Database::connection()->prepare($sql);$s->execute([(int)$u->sub,(int)$u->sub]);Response::json($s->fetchAll());
    }

    public static function updateStatus(int $id): never
    {
        $u=Auth::user();$b=json_decode(file_get_contents('php://input'),true)?:[];$status=$b['status']??'';
        if(!in_array($status,['CONFIRMED','REJECTED'],true)) Response::json(null,422,'status phải là CONFIRMED hoặc REJECTED');
        $pdo=Database::connection();
        $pdo->beginTransaction();
        try {
            $match=$pdo->prepare('SELECT m.id,m.status,m.lost_post_id,m.found_post_id,lp.user_id lost_user_id,fp.user_id found_user_id FROM matches m JOIN posts lp ON lp.id=m.lost_post_id JOIN posts fp ON fp.id=m.found_post_id WHERE m.id=? FOR UPDATE');
            $match->execute([$id]);
            $row=$match->fetch();
            if(!$row || ((int)$row['lost_user_id']!==(int)$u->sub && (int)$row['found_user_id']!==(int)$u->sub)) {
                $pdo->rollBack();
                Response::json(null,404,'Không tìm thấy match hoặc không có quyền');
            }
            if($status==='CONFIRMED' && (int)$row['lost_user_id']!==(int)$u->sub) {
                $pdo->rollBack();
                Response::json(null,403,'Chỉ người đăng bài mất mới được xác nhận');
            }
            if($row['status']!=='PENDING') {
                $pdo->rollBack();
                Response::json(null,409,'Match đã được xử lý trước đó');
            }

            $s=$pdo->prepare('UPDATE matches SET status=? WHERE id=? AND status="PENDING"');
            $s->execute([$status,$id]);
            if($status==='CONFIRMED') {
                $close=$pdo->prepare('UPDATE posts SET status="CLOSED" WHERE id IN (?,?)');
                $close->execute([(int)$row['lost_post_id'],(int)$row['found_post_id']]);
            }
            $pdo->commit();
            Response::json(['id'=>$id,'status'=>$status,'posts_closed'=>$status==='CONFIRMED']);
        } catch(\Throwable $e) {
            if($pdo->inTransaction()) $pdo->rollBack();
            throw $e;
        }
    }
}
