from freeGPT import AsyncClient
from asyncio import run
from loguru import logger

async def send_question(prompt):

    if not prompt == '/stop':
        try:
            logger.info(prompt)
            resp = await AsyncClient.create_completion("gpt3", prompt)

            logger.success('')
            return resp
        except Exception as e:
            logger.error(e)

    return


