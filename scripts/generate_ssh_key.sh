#!/bin/bash

# Скрипт для генерации SSH ключа без passphrase для GitHub Actions

echo "🔑 Генерация SSH ключа для GitHub Actions деплоя..."

# Создаем директорию для ключей
mkdir -p ~/.ssh

# Генерируем SSH ключ без passphrase
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy -N ""

echo ""
echo "✅ SSH ключ сгенерирован!"
echo ""
echo "📋 Приватный ключ (добавьте в GitHub Secret DO_SSH_KEY):"
echo "=================================================="
cat ~/.ssh/github_actions_deploy
echo "=================================================="
echo ""
echo "📋 Публичный ключ (добавьте на сервер в ~/.ssh/authorized_keys):"
echo "=================================================="
cat ~/.ssh/github_actions_deploy.pub
echo "=================================================="
echo ""
echo "📝 Инструкции:"
echo "1. Скопируйте приватный ключ выше в GitHub Secret 'DO_SSH_KEY'"
echo "2. Оставьте GitHub Secret 'DO_SSH_PASSPHRASE' пустым"
echo "3. Добавьте публичный ключ на сервер:"
echo "   ssh root@your-server-ip"
echo "   echo 'ПУБЛИЧНЫЙ_КЛЮЧ_ВЫШЕ' >> ~/.ssh/authorized_keys"
echo "   chmod 600 ~/.ssh/authorized_keys"
echo "   chmod 700 ~/.ssh"
echo ""
echo "🚀 После этого GitHub Actions сможет подключаться к серверу!"