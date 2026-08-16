<?php
namespace App\Middleware;

use App\Services\JwtService;
use App\Services\Response;
use Throwable;

final class Auth
{
    public static function user(): object
    {
        $header = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
        if (!preg_match('/Bearer\s+(\S+)/', $header, $m)) {
            Response::json(null, 401, 'Thiếu access token');
        }
        try {
            return JwtService::decode($m[1]);
        } catch (Throwable) {
            Response::json(null, 401, 'Access token không hợp lệ hoặc đã hết hạn');
        }
    }

    public static function admin(): object
    {
        $user = self::user();
        if (($user->role ?? '') !== 'ADMIN') Response::json(null, 403, 'Yêu cầu quyền ADMIN');
        return $user;
    }
}
