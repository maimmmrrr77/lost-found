<?php
namespace App\Services;

use Firebase\JWT\JWT;
use Firebase\JWT\Key;

final class JwtService
{
    public static function issue(array $user): string
    {
        $now = time();
        $ttl = (int)(getenv('JWT_TTL') ?: 86400);
        return JWT::encode([
            'iat' => $now,
            'exp' => $now + $ttl,
            'sub' => (string)$user['id'],
            'role' => $user['role'],
            'username' => $user['username'],
        ], self::secret(), 'HS256');
    }

    public static function decode(string $token): object
    {
        return JWT::decode($token, new Key(self::secret(), 'HS256'));
    }

    private static function secret(): string
    {
        return getenv('JWT_SECRET') ?: 'dev-secret';
    }
}
