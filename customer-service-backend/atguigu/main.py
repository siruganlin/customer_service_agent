import uvicorn

from atguigu.conf.config import settings

if __name__ == '__main__':

    uvicorn.run(
        app="atguigu.api.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        )
