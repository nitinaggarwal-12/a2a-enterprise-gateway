"""Repository-specific experimental gRPC service implementation.

The protobuf contract is useful for transport experiments but is not asserted to
be the standards-facing A2A v1 contract.
"""

import asyncio
import logging
from typing import AsyncIterator, Dict
import grpc
from google.protobuf import empty_pb2, struct_pb2

from a2a.v1 import a2a_pb2, a2a_pb2_grpc
from .push_dispatcher import dispatch_in_background

logger = logging.getLogger("grpc_services")


class A2AServiceImpl(a2a_pb2_grpc.A2AServiceServicer):
    """Experimental repository-specific gRPC service."""

    MAX_CANCELLED_TASKS = 5000
    CANCEL_EVICT_BATCH = 1000

    def __init__(self):
        self._cancelled_tasks: Dict[str, bool] = {}

    def _record_cancellation(self, task_id: str) -> None:
        """Bound cancellation markers even for arbitrary CancelTask calls."""
        if task_id in self._cancelled_tasks:
            self._cancelled_tasks[task_id] = True
            return
        while len(self._cancelled_tasks) >= self.MAX_CANCELLED_TASKS:
            batch = min(self.CANCEL_EVICT_BATCH, len(self._cancelled_tasks))
            for key in list(self._cancelled_tasks.keys())[:batch]:
                self._cancelled_tasks.pop(key, None)
        self._cancelled_tasks[task_id] = True

    async def ExecuteTask(
        self,
        request: a2a_pb2.ExecuteTaskRequest,
        context: grpc.aio.ServicerContext,
    ) -> a2a_pb2.Task:
        """Execute task synchronously and return final Task object."""
        task_id = request.task_id or "task-default"
        logger.info(f"[ExecuteTask] Received task {task_id}")

        params_dict = dict(request.parameters.fields) if request.parameters else {}
        study_id = "MK-3475-087"
        cohort = "Cohort-B"

        if "studyId" in params_dict:
            study_id = params_dict["studyId"].string_value
        if "cohort" in params_dict:
            cohort = params_dict["cohort"].string_value

        # Build output Struct
        output_struct = struct_pb2.Struct()
        output_struct.update({
            "studyId": study_id,
            "cohort": cohort,
            "variancePct": 2.14,
            "status": "DEMO_COMPLETED",
            "validationStatus": "NOT_REGULATORY_VALIDATION",
            "binaryDeserialization": "Repository-specific Protobuf typed payload",
        })

        input_struct = struct_pb2.Struct()
        if request.parameters:
            input_struct.CopyFrom(request.parameters)

        task = a2a_pb2.Task(
            id=task_id,
            state=a2a_pb2.TaskState.COMPLETED,
            input=input_struct,
            output=output_struct,
            error="",
        )

        # Trigger push if configured
        if request.push_config and request.push_config.url:
            dispatch_in_background(
                url=request.push_config.url,
                task_id=task_id,
                state="COMPLETED",
                output_data={"studyId": study_id, "variancePct": 2.14},
                token=request.push_config.token,
            )

        return task

    async def StreamTask(
        self,
        request: a2a_pb2.ExecuteTaskRequest,
        context: grpc.aio.ServicerContext,
    ) -> AsyncIterator[a2a_pb2.StreamTaskResponse]:
        """Stream progressive clinical dossier reasoning traces and state changes."""
        task_id = request.task_id or "task-stream-001"
        self._cancelled_tasks[task_id] = False

        params_dict = dict(request.parameters.fields) if request.parameters else {}
        study_id = "MK-3475-087"
        cohort = "Cohort-B"
        if "studyId" in params_dict:
            study_id = params_dict["studyId"].string_value
        if "cohort" in params_dict:
            cohort = params_dict["cohort"].string_value

        logger.info(f"[StreamTask] Starting stream for {task_id} (Study: {study_id}, Cohort: {cohort})")

        events = [
            (a2a_pb2.TaskState.SUBMITTED, "Initial task validated against AIP-127 Protobuf schema.", False),
            (a2a_pb2.TaskState.WORKING, f"Connecting to EDC clinical data warehouse for Study {study_id}...", False),
            (a2a_pb2.TaskState.WORKING, f"Extracting adverse event records for {cohort} (MedDRA v26.1)...", False),
            (a2a_pb2.TaskState.WORKING, "Computing Bayesian variance score across primary safety endpoints...", False),
            (a2a_pb2.TaskState.WORKING, "Variance computed: 2.14% elevation in Grade 3 ALT/AST metrics.", False),
            (a2a_pb2.TaskState.WORKING, "Drafting demo Protocol Amendment v4.2 recommendation...", False),
            (a2a_pb2.TaskState.INPUT_REQUIRED, "Dossier complete. Human-in-the-Loop review required by Medical Director.", True),
        ]

        try:
            for state, msg, is_terminal in events:
                if self._cancelled_tasks.get(task_id, False):
                    logger.info(f"[StreamTask] Task {task_id} cancelled during stream.")
                    yield a2a_pb2.StreamTaskResponse(
                        task_id=task_id,
                        chunk_text="Task execution was cancelled by client.",
                        current_state=a2a_pb2.TaskState.CANCELLED,
                        is_terminal=True,
                    )
                    return

                payload_struct = struct_pb2.Struct()
                if is_terminal:
                    payload_struct.update({
                        "studyId": study_id,
                        "cohort": cohort,
                        "variancePct": 2.14,
                        "actionRequired": "SIGN_OFF_AMENDMENT",
                        "requiresHITL": True,
                    })

                response = a2a_pb2.StreamTaskResponse(
                    task_id=task_id,
                    chunk_text=msg,
                    current_state=state,
                    is_terminal=is_terminal,
                    payload=payload_struct,
                )
                yield response
                await asyncio.sleep(0.3)

            # Out-of-band push notification dispatch
            if request.push_config and request.push_config.url:
                dispatch_in_background(
                    url=request.push_config.url,
                    task_id=task_id,
                    state="INPUT_REQUIRED",
                    output_data={"studyId": study_id, "cohort": cohort, "variancePct": 2.14},
                    token=request.push_config.token,
                )
        finally:
            self._cancelled_tasks.pop(task_id, None)

    async def CancelTask(
        self,
        request: a2a_pb2.CancelTaskRequest,
        context: grpc.aio.ServicerContext,
    ) -> empty_pb2.Empty:
        """Cancel an in-flight streaming or background task."""
        task_id = request.task_id
        logger.info(f"[CancelTask] Cancelling task {task_id}. Reason: {request.reason}")
        self._record_cancellation(task_id)
        return empty_pb2.Empty()
