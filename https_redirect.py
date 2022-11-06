import uvicorn
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import RedirectResponse

https_redirect_app = FastAPI(
    docs_url=None,
    redoc_url=None
)


@https_redirect_app.route('/{_:path}')
async def https_redirect(request: Request):
    return RedirectResponse(request.url.replace(scheme='https'))

if __name__ == '__main__':
    uvicorn.run('https_redirect:https_redirect_app', port=80, host='0.0.0.0')