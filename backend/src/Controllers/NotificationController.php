<?php
namespace App\Controllers;

use App\Config\Database;
use App\Middleware\Auth;
use App\Services\Response;

final class NotificationController
{
    public static function mine(): never
    {
        $u=Auth::user();$s=Database::connection()->prepare('SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 100');$s->execute([(int)$u->sub]);Response::json($s->fetchAll());
    }
    public static function read(int $id): never
    {
        $u=Auth::user();$s=Database::connection()->prepare('UPDATE notifications SET is_read=1 WHERE id=? AND user_id=?');$s->execute([$id,(int)$u->sub]);Response::json(['id'=>$id,'is_read'=>true]);
    }
}
