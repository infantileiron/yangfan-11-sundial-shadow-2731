from fastapi import APIRouter, HTTPException

from src.config.settings import Session
from src.constants.workflow import Stage
from src.services.runs import require

from .stencil import workshop_stencil

router = APIRouter()


@router.get("/domain/shadow-stencil/{run_id}", summary="读取按模拟时刻排序的影线放样单")
def read_stencil(run_id: str):
    with Session() as db:
        run = require(db, run_id)
        if run.status != Stage.SUCCEEDED.value or run.result is None:
            raise HTTPException(409, "计算完成后才能生成影线放样单。")
        return {"run_id": run.id, **workshop_stencil(run.result["rows"])}
