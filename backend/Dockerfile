FROM php:8.3-apache
RUN apt-get update && apt-get install -y --no-install-recommends unzip \
    && rm -rf /var/lib/apt/lists/*
RUN docker-php-ext-install pdo pdo_mysql && a2enmod rewrite headers
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer
WORKDIR /var/www/html/backend
COPY composer.json composer.lock* ./
RUN composer install --no-interaction --prefer-dist
COPY . .
COPY apache.conf /etc/apache2/sites-available/000-default.conf
RUN mkdir -p /var/www/html/uploads && chown -R www-data:www-data /var/www/html/uploads
EXPOSE 80