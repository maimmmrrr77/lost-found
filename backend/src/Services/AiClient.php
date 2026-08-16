<?php
namespace App\Services;

final class AiClient
{
    public static function similarity(array $lostPost, array $foundPost): float
    {
        $url = rtrim(getenv('AI_SERVICE_URL') ?: 'http://localhost:8001', '/') . '/similarity';
        $payload = json_encode([
            'lost' => self::aiPayload($lostPost),
            'found' => self::aiPayload($foundPost),
        ], JSON_UNESCAPED_UNICODE);

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS => $payload,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 8,
        ]);
        $raw = curl_exec($ch);
        $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($status >= 200 && $status < 300 && $raw) {
            $json = json_decode($raw, true);
            return (float)($json['similarity'] ?? 0);
        }
        return 0.0;
    }

    private static function aiPayload(array $post): array
    {
        return [
            'title' => $post['title'] ?? '',
            'description' => $post['description'] ?? '',
            'color' => $post['color'] ?? '',
            'brand' => $post['brand'] ?? '',
            'location' => $post['location'] ?? '',
            'category_id' => $post['category_id'] ?? null,
        ];
    }
}
