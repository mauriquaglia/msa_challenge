from fastapi import FastAPI, HTTPException
from typing import List
from pymongo import MongoClient
from bson import ObjectId
from pydantic import BaseModel, Field

from time import time
import httpx
import asyncio
import json
import random
from bson.json_util import dumps, loads
import math
import datetime
import os
import logging

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class Muscles(BaseModel):
	name: str

class Equipment(BaseModel):
	name: str

class Exercises(BaseModel):
    name: str
    description: str
    muscles: List[Muscles] = []
    equipment: List[Equipment] = []

class Category(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    category: str = ""
    exercises: List[Exercises] = []

category = Category()

class Muscles2(BaseModel):
    id: int
    name: str

class Equipment2(BaseModel):
    id: int
    name: str

class Exercises2(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: str
    category: str
    id_category: int
    muscles: List[Muscles] = []
    equipment: List[Equipment] = []
    class Config:
        arbitrary_types_allowed = True

objeto = []

def append(x, get = False):
    if get == False : objeto.append(x)
    if get == True : 
        return objeto
    else: return False

def create_obj(name, category):
    category.category = name
    category.exercises = category.exercises
    return category.dict()
    

app = FastAPI()


async def request(client, URL):
    response = await client.get(URL)
    return  json.loads(response.text)


async def task(url = "https://wger.de/api/v2/exerciseinfo/?limit=1"):
    async with httpx.AsyncClient() as client:
        #tasks = [request(client) for i in range(1)]
        tasks = request(client, url)
        #result = await asyncio.gather(*tasks)
        result = await asyncio.gather(tasks)
        return result
        #print(result)



mongo_user = os.environ.get('DB_USER', 'user')
mongo_pass = os.environ.get('DB_PASS', 'pass')
mongo_host = os.environ.get('DB_HOST', 'cluster.com')

mongodb_uri = 'mongodb+srv://' + mongo_user + ':' + mongo_pass + '@' + mongo_host + '/?retryWrites=true&w=majority'

#client = MongoClient(mongodb_uri, port)
client = MongoClient(mongodb_uri)
db = client['msa']

@app.get("/")
async def root():
    try:
        start = time()
        count = await task()
        count = count[0]['count']
        counter = 0
        result = await task("https://wger.de/api/v2/exerciseinfo/?limit="+str(count))

        for x in result[0]['results']:
            if x['category']['name'] == 'Abs': 
                counter=counter+1
                append(Exercises2(name= x['name'], 
                description= x['description'], 
                category=x['category']['name'], 
                id_category=x['category']['id'] ,
                muscles=x['muscles'],
                equipment=x['equipment']).dict())
    
        result = append('', True)
        #db.exercises.insert_many(result)
        logging.info('GET /')
        return {"message": time() - start, "count": counter}
    except Exception as ex:
        logging.exception(ex)
        raise

@app.get("/import_category/{name}")
async def import_category(name: str):
    try:
        start = time()
        count = await task()
        count = count[0]['count']
        counter = 0
        result = await task("https://wger.de/api/v2/exerciseinfo/?limit="+str(count))

        for x in result[0]['results']:
            if x['category']['name'] == name: 
                counter=counter+1
                append(Exercises2(name= x['name'], 
                description= x['description'], 
                category=x['category']['name'], 
                id_category=x['category']['id'] ,
                muscles=x['muscles'],
                equipment=x['equipment']).dict())
    
        result = append('', True)
        if len(result) > 0 :
            db.exercises.delete_many({"category": name})
            db.exercises.insert_many(result)
        logging.info('GET /import_category/' + name)
        return {"message": "Import OK","time": time() - start, "count": counter}
    except Exception as ex:
        logging.exception(ex)
        raise


@app.put("/import_category2/{name}")
async def import_category2(name: str, category: Category):
    try:
        #print("ver {recuento} ")
        if (recuento :=  db.data.find_one({"category": name})) is not None:
            raise HTTPException(status_code=400, detail="La categoria " + name + " ya existe")
        data = create_obj(name, category)
        db.data.insert_one(data)
        logging.info('GET /import_category/' + name)
        return {"name": name, "category": category}
    except Exception as ex:
        logging.exception(ex)
        raise


@app.get("/get_routine/{days}")
async def get_routine(days: int):
    try:
        categorys = db.exercises.distinct('category')
        categorys = random.sample( categorys, len(categorys) )
        exercises_of_categorys = []
        categorys_of_day = []

        schedule = []
        for x in range(days*3):

            var = loads(dumps(db.exercises.find({"category": categorys[(x+1) % len(categorys)]}).limit(10)))
            var = random.sample( var, len(var) )
            for i in range(3) :
                #exercises_of_categorys.append({"name": var[i]['name'], "description": var[i]['description'], "muscles": var[i]['muscles'], "equipment": var[i]['equipment'] })
                exercises_of_categorys.append({"category": var[i]['category'], "name": var[i]['name'] })

            categorys_of_day.append({"category": categorys[(x+1) % len(categorys)], "exercises": exercises_of_categorys})
            exercises_of_categorys = []

            if (x+1) % 3 == 0 :
                #print((x+1) % len(categorys))
                #print(categorys[(x+1) % len(categorys)])
                #categorys_of_day.append({"category": categorys[(x+1) % len(categorys)], "exercises": exercises_of_categorys})
                schedule.append({"day_of_week": math.ceil((x+1)/3),"training":  categorys_of_day})
                categorys_of_day = []
            #if (x+1) % 3 == 0 : schedule.append({"day_of_week": math.ceil((x+1)/3), categorys_of_day})
        logging.info('GET /import_category/' + str(days))
        return {"date": datetime.datetime.now(), "schedule": schedule}
    except Exception as ex:
        logging.exception(ex)
        raise
