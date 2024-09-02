c.NotebookApp.tornado_settings = {
    'headers': {
        'Content-Security-Policy': "frame-ancestors self http://localhost",
    }
}
c.ServerApp.allow_origin = 'http://localhost'  
c.ServerApp.allow_credentials = True
c.ServerApp.disable_check_xsrf = True
c.ServerApp.trust_xheaders = True
c.ServerApp.allow_remote_access = True
c.ServerApp.token = 'my_fixed_token123' 
c.ServerApp.open_browser = False
c.NotebookApp.notebook_dir = '/home/jovyan/work'
c.ServerApp.root_dir = '/home/jovyan/work'
