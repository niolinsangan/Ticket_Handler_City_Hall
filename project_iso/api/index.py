import json
from app import app

def run_serverless(event, context):
    """Vercel Python serverless handler for Flask app"""
    from werkzeug.wrappers import Request
    from werkzeug.test import Client
    from werkzeug.wsgi import responder
    
    # Create WSGI client
    client = Client(app, wrapper=responder)
    
    # Build Request from Vercel event
    req = Request.from_values(
        path=event.get('path', '/'),
        method=event.get('method', 'GET'),
        headers=dict(event.get('headers', {})),
        data=event.get('body', b''),
        query_string=event.get('queryString', {})
    )
    
    # Handle the request
    resp = client.get(req.path, req.environ)
    
    # Return Vercel response format
    return {
        'statusCode': resp.status_code,
        'headers': dict(resp.headers),
        'body': resp.data.decode('utf-8')
    }

handler = run_serverless
