<?php
namespace App\Controllers;

use App\Config\Database;
use App\Middleware\Auth;
use App\Services\JwtService;
use App\Services\Response;
use PDOException;

final class AuthController
{
    public static function register(): never
    {
        $b = self::body();
        foreach (['full_name','username','email','password'] as $f) {
            if (empty($b[$f])) Response::json(null, 422, "Thiếu trường {$f}");
        }
        if (!filter_var($b['email'], FILTER_VALIDATE_EMAIL)) Response::json(null, 422, 'Email không hợp lệ');
        if (strlen($b['password']) < 8) Response::json(null, 422, 'Mật khẩu tối thiểu 8 ký tự');

        try {
            $pdo = Database::connection();
            $stmt = $pdo->prepare('INSERT INTO users(full_name, username, email, phone, password, role, status, created_at) VALUES(?,?,?,?,?,"USER",1,NOW())');
            $stmt->execute([
                trim($b['full_name']), trim($b['username']), strtolower(trim($b['email'])),
                $b['phone'] ?? null, password_hash($b['password'], PASSWORD_DEFAULT)
            ]);
            $id = (int)$pdo->lastInsertId();
            Response::json(['id' => $id], 201, 'Đăng ký thành công');
        } catch (PDOException $e) {
            if ((int)$e->errorInfo[1] === 1062) Response::json(null, 409, 'Username hoặc email đã tồn tại');
            throw $e;
        }
    }

    public static function login(): never
    {
        $b = self::body();
        $identity = trim($b['identity'] ?? '');
        $password = $b['password'] ?? '';
        $stmt = Database::connection()->prepare('SELECT * FROM users WHERE (email=? OR username=?) LIMIT 1');
        $stmt->execute([$identity, $identity]);
        $user = $stmt->fetch();
        if (!$user || !password_verify($password, $user['password'])) Response::json(null, 401, 'Sai tài khoản hoặc mật khẩu');
        if (!(int)$user['status']) Response::json(null, 403, 'Tài khoản đã bị khóa');
        unset($user['password']);
        Response::json(['token' => JwtService::issue($user), 'user' => $user], 200, 'Đăng nhập thành công');
    }

    public static function me(): never
    {
        $claims = Auth::user();
        $stmt = Database::connection()->prepare('SELECT id,full_name,username,email,phone,avatar,role,status,created_at FROM users WHERE id=?');
        $stmt->execute([(int)$claims->sub]);
        Response::json($stmt->fetch());
    }

    private static function body(): array
    {
        $body = json_decode(file_get_contents('php://input'), true);
        return is_array($body) ? $body : [];
    }
}
