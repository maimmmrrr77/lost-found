<?php
namespace App\Controllers;

use App\Config\Database;
use App\Middleware\Auth;
use App\Services\Response;
use PDOException;

final class AdminController
{
    /* ---------------- THỐNG KÊ ---------------- */

    public static function stats(): never
    {
        Auth::admin();
        $pdo = Database::connection();
        $one = fn(string $sql): int => (int)$pdo->query($sql)->fetchColumn();

        Response::json([
            'total_users'      => $one('SELECT COUNT(*) FROM users'),
            'locked_users'     => $one('SELECT COUNT(*) FROM users WHERE status=0'),
            'total_posts'      => $one('SELECT COUNT(*) FROM posts'),
            'open_posts'       => $one('SELECT COUNT(*) FROM posts WHERE status="OPEN"'),
            'closed_posts'     => $one('SELECT COUNT(*) FROM posts WHERE status="CLOSED"'),
            'lost_posts'       => $one('SELECT COUNT(*) FROM posts WHERE post_type="LOST"'),
            'found_posts'      => $one('SELECT COUNT(*) FROM posts WHERE post_type="FOUND"'),
            'total_matches'    => $one('SELECT COUNT(*) FROM matches'),
            'pending_matches'  => $one('SELECT COUNT(*) FROM matches WHERE status="PENDING"'),
            'confirmed_matches'=> $one('SELECT COUNT(*) FROM matches WHERE status="CONFIRMED"'),
            'total_categories' => $one('SELECT COUNT(*) FROM categories'),
            'total_images'     => $one('SELECT COUNT(*) FROM images'),
        ]);
    }

    /* ---------------- NGƯỜI DÙNG ---------------- */

    public static function users(): never
    {
        Auth::admin();
        $sql = 'SELECT u.id, u.full_name, u.username, u.email, u.phone, u.role, u.status, u.created_at,
                       (SELECT COUNT(*) FROM posts p WHERE p.user_id = u.id) AS post_count
                FROM users u ORDER BY u.id DESC LIMIT 500';
        Response::json(Database::connection()->query($sql)->fetchAll());
    }

    public static function updateUserStatus(int $id): never
    {
        $admin = Auth::admin();
        $body   = json_decode(file_get_contents('php://input'), true) ?: [];

        if (!array_key_exists('status', $body)) {
            Response::json(null, 422, 'Thiếu trường status');
        }
        $status = (int)((bool)$body['status']);

        if ((int)$admin->sub === $id) {
            Response::json(null, 422, 'Không thể tự khóa tài khoản của chính mình');
        }

        $pdo  = Database::connection();
        $stmt = $pdo->prepare('SELECT role FROM users WHERE id=?');
        $stmt->execute([$id]);
        $user = $stmt->fetch();

        if (!$user) {
            Response::json(null, 404, 'Không tìm thấy người dùng');
        }
        if ($user['role'] === 'ADMIN') {
            Response::json(null, 403, 'Không thể thay đổi trạng thái của một quản trị viên');
        }

        $upd = $pdo->prepare('UPDATE users SET status=? WHERE id=?');
        $upd->execute([$status, $id]);

        Response::json(
            ['id' => $id, 'status' => $status],
            200,
            $status ? 'Đã mở khóa tài khoản' : 'Đã khóa tài khoản'
        );
    }

    /* ---------------- DANH MỤC ---------------- */

    public static function categories(): never
    {
        Auth::admin();
        $sql = 'SELECT c.id, c.name, c.description, c.status,
                       (SELECT COUNT(*) FROM posts p WHERE p.category_id = c.id) AS post_count
                FROM categories c ORDER BY c.id';
        Response::json(Database::connection()->query($sql)->fetchAll());
    }

    public static function createCategory(): never
    {
        Auth::admin();
        $body = json_decode(file_get_contents('php://input'), true) ?: [];

        $name = trim($body['name'] ?? '');
        if ($name === '') {
            Response::json(null, 422, 'Thiếu tên danh mục');
        }

        try {
            $pdo  = Database::connection();
            $stmt = $pdo->prepare('INSERT INTO categories(name, description, status) VALUES(?,?,1)');
            $stmt->execute([$name, $body['description'] ?? null]);
            Response::json(['id' => (int)$pdo->lastInsertId()], 201, 'Đã thêm danh mục');
        } catch (PDOException $e) {
            if ((int)$e->errorInfo[1] === 1062) {
                Response::json(null, 409, 'Tên danh mục đã tồn tại');
            }
            throw $e;
        }
    }

    public static function updateCategory(int $id): never
    {
        Auth::admin();
        $body = json_decode(file_get_contents('php://input'), true) ?: [];

        $fields = [];
        $params = [];
        if (isset($body['name']) && trim($body['name']) !== '') {
            $fields[] = 'name=?';
            $params[] = trim($body['name']);
        }
        if (array_key_exists('description', $body)) {
            $fields[] = 'description=?';
            $params[] = $body['description'];
        }
        if (array_key_exists('status', $body)) {
            $fields[] = 'status=?';
            $params[] = (int)((bool)$body['status']);
        }
        if (!$fields) {
            Response::json(null, 422, 'Không có trường nào để cập nhật');
        }

        $params[] = $id;
        try {
            $stmt = Database::connection()->prepare('UPDATE categories SET ' . implode(',', $fields) . ' WHERE id=?');
            $stmt->execute($params);
            if ($stmt->rowCount() === 0) {
                Response::json(['id' => $id], 200, 'Không có thay đổi nào được ghi nhận');
            }
            Response::json(['id' => $id], 200, 'Đã cập nhật danh mục');
        } catch (PDOException $e) {
            if ((int)$e->errorInfo[1] === 1062) {
                Response::json(null, 409, 'Tên danh mục đã tồn tại');
            }
            throw $e;
        }
    }

    /* ---------------- BÀI ĐĂNG ---------------- */

    public static function posts(): never
    {
        Auth::admin();
        $pdo    = Database::connection();
        $where  = [];
        $params = [];

        foreach (['post_type', 'category_id', 'status'] as $f) {
            if (isset($_GET[$f]) && $_GET[$f] !== '') {
                $where[]  = "p.{$f} = ?";
                $params[] = $_GET[$f];
            }
        }
        if (!empty($_GET['q'])) {
            $where[] = '(p.title LIKE ? OR p.description LIKE ? OR u.full_name LIKE ?)';
            $q = '%' . $_GET['q'] . '%';
            array_push($params, $q, $q, $q);
        }

        $sql = 'SELECT p.id, p.post_type, p.title, p.location, p.event_date, p.status, p.created_at,
                       c.name AS category_name, u.full_name AS owner_name, u.id AS owner_id,
                       (SELECT COUNT(*) FROM images i WHERE i.post_id = p.id) AS image_count
                FROM posts p
                JOIN categories c ON c.id = p.category_id
                JOIN users u ON u.id = p.user_id'
             . ($where ? ' WHERE ' . implode(' AND ', $where) : '')
             . ' ORDER BY p.created_at DESC LIMIT 300';

        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);
        Response::json($stmt->fetchAll());
    }

    public static function deletePost(int $id): never
    {
        Auth::admin();
        $stmt = Database::connection()->prepare('DELETE FROM posts WHERE id=?');
        $stmt->execute([$id]);

        if ($stmt->rowCount() === 0) {
            Response::json(null, 404, 'Không tìm thấy bài đăng');
        }
        Response::json(['id' => $id], 200, 'Đã xóa bài đăng');
    }
}
