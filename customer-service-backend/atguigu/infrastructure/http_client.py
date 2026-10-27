import asyncio
import httpx


# 同步方式
# r = httpx.get('http://localhost:18081/users/u1001/orders')
# print(r.json())

# 异步方式
# async def main():

#     # await：表示waait代码块结束后，自动调用close方法，关闭远程请求
#     async with httpx.AsyncClient() as client:
#          response= await client.get('http://localhost:18081/users/u1001/orders')
#          print(response.json())
#
# asyncio.run(main())

# 优化
# 定义全局变量
http_client: httpx.AsyncClient | None = None


# 初始化http客户端
def init_http_client():
    global http_client # 声明
    http_client = httpx.AsyncClient()

# 关闭资源
async def close_http_client():
    if http_client is not None:
        await http_client.aclose()
