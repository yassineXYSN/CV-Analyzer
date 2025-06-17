from fastapi import FastAPI, Path, HTTPException
from pydantic import BaseModel

app = FastAPI()

cars = {
    1: {"Make": "BMW", "Model": "M3", "Year": 2020, "Color": "Grey"},
    2: {"Make": "Audi", "Model": "RS5", "Year": 2021, "Color": "Red"},
    3: {"Make": "Mercedes-Benz", "Model": "C63 AMG", "Year": 2019, "Color": "Black"},
    4: {"Make": "Tesla", "Model": "Model S", "Year": 2022, "Color": "White"},
    5: {"Make": "Porsche", "Model": "911 Carrera", "Year": 2023, "Color": "Blue"},
    6: {"Make": "Toyota", "Model": "Supra", "Year": 2020, "Color": "Yellow"},
    7: {"Make": "Ford", "Model": "Mustang GT", "Year": 2018, "Color": "Orange"},
    8: {"Make": "Chevrolet", "Model": "Camaro SS", "Year": 2021, "Color": "Green"},
    9: {"Make": "BMW", "Model": "M4", "Year": 2018, "Color": "Blue"}
}

class Car(BaseModel):
    Make: str
    Model: str
    Year: int
    Color: str

@app.get("/", response_model=dict)
def welcome():
    return {"message": "Hello World"}

@app.get("/cars/{car_id}", response_model=Car)
def read_car(car_id: int = Path(..., ge=1, le=9)):
    return cars[car_id]

@app.get("/get", response_model=dict)
def get_make(make: str):
    cars_to_return = {}
    for car_id, car in cars.items():
        if car["Make"] == make:
            cars_to_return[car_id] = car
    return cars_to_return

@app.post("/add/{car_id}", response_model=Car)
def add_car(car_id: int, car: Car):
    if car_id not in cars:
        cars[car_id] = car.dict()
        return cars[car_id]
    return {"message": "id already exists"}
