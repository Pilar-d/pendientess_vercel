from app import app

def handler(request, response):
    # Simular entorno WSGI para Vercel
    environ = {
        'REQUEST_METHOD': request.method,
        'PATH_INFO': request.path,
        'QUERY_STRING': request.query_string,
        'SERVER_NAME': 'vercel',
        'SERVER_PORT': '80',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': None,
        'wsgi.errors': None,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False
    }
    
    # Ejecutar la aplicación Flask
    result = app(environ, lambda status, headers: None)
    
    # Configurar respuesta
    response.status = 200
    response.send(b''.join(result))