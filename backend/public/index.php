<?php
require __DIR__.'/../vendor/autoload.php';
require __DIR__.'/../config/database.php';

use App\Controllers\AdminController;
use App\Controllers\AuthController;
use App\Controllers\CategoryController;
use App\Controllers\PostController;
use App\Controllers\MatchController;
use App\Controllers\NotificationController;
use App\Services\Response;

header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type, Authorization');
header('Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS');
if($_SERVER['REQUEST_METHOD']==='OPTIONS'){http_response_code(204);exit;}

$method=$_SERVER['REQUEST_METHOD'];
$path=trim($_GET['path'] ?? '', '/');

try {
    if($method==='GET' && $path==='health') Response::json(['status'=>'ok']);

    /* ---- Xác thực ---- */
    if($method==='POST' && $path==='auth/register') AuthController::register();
    if($method==='POST' && $path==='auth/login') AuthController::login();
    if($method==='GET' && $path==='auth/me') AuthController::me();

    /* ---- Danh mục ---- */
    if($method==='GET' && $path==='categories') CategoryController::index();

    /* ---- Bài đăng ---- */
    if($method==='GET' && $path==='posts') PostController::index();
    if($method==='POST' && $path==='posts') PostController::create();
    if($method==='GET' && $path==='posts/mine') PostController::myPosts();
    if($method==='GET' && preg_match('#^posts/(\d+)$#',$path,$m)) PostController::show((int)$m[1]);
    if($method==='POST' && preg_match('#^posts/(\d+)/images$#',$path,$m)) PostController::uploadImage((int)$m[1]);
    if($method==='PATCH' && preg_match('#^posts/(\d+)/close$#',$path,$m)) PostController::close((int)$m[1]);

    /* ---- Kết quả so khớp AI ---- */
    if($method==='GET' && $path==='matches/mine') MatchController::mine();
    if($method==='PATCH' && preg_match('#^matches/(\d+)$#',$path,$m)) MatchController::updateStatus((int)$m[1]);

    /* ---- Thông báo ---- */
    if($method==='GET' && $path==='notifications') NotificationController::mine();
    if($method==='PATCH' && preg_match('#^notifications/(\d+)/read$#',$path,$m)) NotificationController::read((int)$m[1]);

    /* ---- Quản trị (yêu cầu vai trò ADMIN) ---- */
    if($method==='GET' && $path==='admin/stats') AdminController::stats();
    if($method==='GET' && $path==='admin/users') AdminController::users();
    if($method==='PATCH' && preg_match('#^admin/users/(\d+)/status$#',$path,$m)) AdminController::updateUserStatus((int)$m[1]);
    if($method==='GET' && $path==='admin/categories') AdminController::categories();
    if($method==='POST' && $path==='admin/categories') AdminController::createCategory();
    if($method==='PATCH' && preg_match('#^admin/categories/(\d+)$#',$path,$m)) AdminController::updateCategory((int)$m[1]);
    if($method==='GET' && $path==='admin/posts') AdminController::posts();
    if($method==='DELETE' && preg_match('#^admin/posts/(\d+)$#',$path,$m)) AdminController::deletePost((int)$m[1]);

    Response::json(null,404,'API endpoint không tồn tại');
} catch(Throwable $e){
    $debug=(getenv('APP_DEBUG')?:'false')==='true';
    Response::json($debug?['error'=>$e->getMessage(),'trace'=>$e->getTraceAsString()]:null,500,'Lỗi máy chủ');
}
