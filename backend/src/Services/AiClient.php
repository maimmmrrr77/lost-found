<?php
namespace App\Services;

final class AiClient
{
    /**
     * So khớp hai bài đăng LOST và FOUND
     */
    public static function similarity(array $lostPost, array $foundPost): float
    {
        $url = rtrim(getenv('AI_SERVICE_URL') ?: 'http://localhost:8001', '/') . '/similarity';
        $payload = json_encode([
            'lost' => self::aiPayload($lostPost),
            'found' => self::aiPayload($foundPost),
            'model' => 'multimodal-v1' // Sử dụng mô hình kết hợp trọng số mới
        ], JSON_UNESCAPED_UNICODE);

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS => $payload,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 10,
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

    /**
     * Gọi API trích xuất vector ảnh từ ai-service khi người dùng tải ảnh lên
     */
    public static function extractImageFeature(string $absoluteImagePath): ?array
    {
        $url = rtrim(getenv('AI_SERVICE_URL') ?: 'http://localhost:8001', '/') . '/extract-image-feature';
        $payload = json_encode(['image_path' => $absoluteImagePath]);

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS => $payload,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 15,
        ]);
        $raw = curl_exec($ch);
        $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($status >= 200 && $status < 300 && $raw) {
            $json = json_decode($raw, true);
            return $json['embedding'] ?? null;
        }
        return null;
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
            'event_date' => $post['event_date'] ?? null,
            'image_embedding' => $post['image_embedding'] ?? null, // Vector mảng float (nếu có)
        ];
    }
}