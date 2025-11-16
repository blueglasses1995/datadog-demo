FROM nginx:alpine

# Nginx設定ファイルをコピー
COPY nginx.conf /etc/nginx/nginx.conf

# ログディレクトリを作成
RUN mkdir -p /var/log/nginx

# ポート80を公開
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
