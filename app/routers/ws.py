import uuid

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import decode_access_token
from app.core.ws_manager import manager
from app.models import Submission, User

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/submissions/{submission_id}")
async def submission_ws(
    websocket: WebSocket,
    submission_id: uuid.UUID,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    # Browsers can't set a custom Authorization header on a WebSocket
    # handshake -- token comes in as a query param instead. Same JWT
    # validation as everywhere else, just a different transport.
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
    except JWTError:
        await websocket.close(code=4401)
        return

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        await websocket.close(code=4401)
        return

    sub_result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = sub_result.scalar_one_or_none()
    if submission is None:
        await websocket.close(code=4404)
        return
    if submission.user_id != user.id and not user.is_admin:
        await websocket.close(code=4403)
        return

    await manager.connect(str(submission_id), websocket)
    try:
        # Race-condition fallback: if judging already finished before
        # this client connected, pub/sub already fired and won't replay
        # -- so check current state directly and send it immediately.
        if submission.overall_verdict is not None:
            await websocket.send_json(
                {"submission_id": str(submission_id), "overall_verdict": submission.overall_verdict}
            )

        while True:
            # We don't expect the client to send anything meaningful;
            # this just blocks until the client disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(str(submission_id), websocket)
