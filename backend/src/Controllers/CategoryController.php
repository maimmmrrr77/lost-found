<?php
namespace App\Controllers;

use App\Config\Database;
use App\Services\Response;

final class CategoryController
{
    public static function index(): never
    {
        $rows = Database::connection()->query('SELECT id,name,description,status FROM categories WHERE status=1 ORDER BY name')->fetchAll();
        Response::json($rows);
    }
}
