from flask import Flask, render_template, request, jsonify, redirect, url_for

@app.route('/telegram-auth')
def telegram_auth():
    return render_template('telegram_auth.html')

@app.route('/api/telegram-auth', methods=['POST'])
def handle_telegram_auth():
    data = request.json
    phone = data.get('phone')
    code = data.get('code')
    password = data.get('password')
    
    # Здесь будет логика проверки данных Telegram
    # После успешной проверки можно сохранить данные в сессии или базе данных
    
    return jsonify({'success': True}) 