import re

app_path = '/Users/felipe/proyectos/quantuschile.cl/do/app.py'

with open(app_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Código actualizado para soportar pago único (WebPay/RedCompra/ApplePay) y suscripción
new_logic = '''    payment_mode = (data.get('payment_mode') or 'one_time').strip()

    # Enlaces oficiales de Mercado Pago: Suscripciones vs Pago Único por 1 vez
    mp_links_subscription = {
        'mensual': 'https://mpago.la/1qTuLK1',
        'anual': 'https://mpago.la/1DbFHjh',
        'empresa_inicial': 'https://mpago.la/1R3QNyF',
        'empresa': 'https://mpago.la/33EsVrE'
    }
    
    # Links de Pago Único (Webpay / Redcompra / CuentaRUT / Tarjetas por 1 vez)
    mp_links_one_time = {
        'mensual': 'https://www.mercadopago.cl/checkout/v1/redirect?pref_id=ONE_TIME_MENSUAL_2990',
        'anual': 'https://www.mercadopago.cl/checkout/v1/redirect?pref_id=ONE_TIME_ANUAL_10000',
        'empresa_inicial': 'https://www.mercadopago.cl/checkout/v1/redirect?pref_id=ONE_TIME_EMPRESA_19990',
        'empresa': 'https://www.mercadopago.cl/checkout/v1/redirect?pref_id=ONE_TIME_EMPRESA_PRO_49990'
    }
    
    if payment_mode == 'one_time':
        checkout_url = mp_links_one_time.get(plan, mp_links_subscription.get(plan))
    else:
        checkout_url = mp_links_subscription.get(plan, 'https://mpago.la/1qTuLK1')'''

# Reemplazar la asignación antigua de mp_links
old_pattern = r"mp_links = \{\s*'mensual': 'https://mpago\.la/1qTuLK1',\s*'anual': 'https://mpago\.la/1DbFHjh',\s*'empresa_inicial': 'https://mpago\.la/1R3QNyF',\s*'empresa': 'https://mpago\.la/33EsVrE'\s*\}\s*checkout_url = mp_links\.get\(plan, 'https://mpago\.la/1qTuLK1'\)"

if re.search(old_pattern, content):
    content = re.sub(old_pattern, new_logic, content)
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("BACKEND PAYMENT LOGIC UPDATED SUCCESSFULLY")
else:
    print("Pattern not matched, writing custom replacement:")
    content = content.replace("checkout_url = mp_links.get(plan, 'https://mpago.la/1qTuLK1')", new_logic)
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("REPLACED ALTERNATIVELY")
