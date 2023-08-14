
async def run_mongo_test(mongo_database_manager, **kwargs):
    from jonbot.tests.test_mongo_database import test_mongo_database
    return await test_mongo_database(mongo_database_manager, **kwargs)