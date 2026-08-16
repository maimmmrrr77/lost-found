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
        $sql='SELECT m.*, lp.title lost_title, fp.title found_title FROM matches m JOIN posts lp ON lp.id=m.lost_post_id JOIN posts fp ON fp.id=m.found_post_id WHERE lp.user_id=? OR fp.user_id=? ORDER BY m.similarity_score DESC,m.created_at DESC';
        $s=Database::connection()->prepare($sql);$s->execute([(int)$u->sub,(int)$u->sub]);Response::json($s->fetchAll());
    }

    public static function updateStatus(int $id): never
    {
        $u=Auth::user();$b=json_decode(file_get_contents('php://input'),true)?:[];$status=$b['status']??'';
        if(!in_array($status,['CONFIRMED','REJECTED'],true)) Response::json(null,422,'status phải là CONFIRMED hoặc REJECTED');
        $pdo=Database::connection();
        $sql='UPDATE matches m JOIN posts lp ON lp.id=m.lost_post_id JOIN posts fp ON fp.id=m.found_post_id SET m.status=? WHERE m.id=? AND (lp.user_id=? OR fp.user_id=?)';
        $s=$pdo->prepare($sql);$s->execute([$status,$id,(int)$u->sub,(int)$u->sub]);
        if(!$s->rowCount()) Response::json(null,404,'Không tìm thấy match hoặc không có quyền');
        Response::json(['id'=>$id,'status'=>$status]);
    }
}
