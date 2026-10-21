import os
from datetime import datetime
from enum import StrEnum
from itertools import count

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator

app = FastAPI(title="ShiftSwap Board")


class Venue(StrEnum):
    gammage = "gammage"
    athletics = "athletics"


class ShiftIn(BaseModel):
    venue: Venue
    role: str = Field(min_length=2, max_length=40)
    start: datetime
    end: datetime
    posted_by: str = Field(min_length=2, max_length=40)

    @model_validator(mode="after")
    def check_times(self):
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self


class Shift(ShiftIn):
    id: int
    claimed_by: str | None = None


class ClaimIn(BaseModel):
    name: str = Field(min_length=2, max_length=40)


shifts: dict[int, Shift] = {}
ids = count(1)


def reset():
    global ids
    shifts.clear()
    ids = count(1)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"commit": os.getenv("GIT_SHA", "dev")}


@app.post("/shifts", status_code=201)
def post_shift(data: ShiftIn) -> Shift:
    for s in shifts.values():
        if s.posted_by == data.posted_by and s.start < data.end and data.start < s.end:
            raise HTTPException(409, "you already posted an overlapping shift")
    shift = Shift(id=next(ids), **data.model_dump())
    shifts[shift.id] = shift
    return shift


@app.get("/shifts")
def list_shifts(venue: Venue | None = None, open_only: bool = True) -> list[Shift]:
    result = [s for s in shifts.values() if venue is None or s.venue == venue]
    if open_only:
        result = [s for s in result if s.claimed_by is None]
    return sorted(result, key=lambda s: s.start)


@app.post("/shifts/{shift_id}/claim")
def claim_shift(shift_id: int, data: ClaimIn) -> Shift:
    shift = shifts.get(shift_id)
    if shift is None:
        raise HTTPException(404, "shift not found")
    if shift.claimed_by is not None:
        raise HTTPException(409, "shift already claimed")
    if shift.posted_by == data.name:
        raise HTTPException(400, "you cannot claim your own shift")
    for s in shifts.values():
        if s.claimed_by == data.name and s.start < shift.end and shift.start < s.end:
            raise HTTPException(409, "this overlaps a shift you already claimed")
    shift.claimed_by = data.name
    return shift
