from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import RedirectResponse, FileResponse, JSONResponse
# import json
# import logging
from scansheet_agent import ScanSheetAgent, PromptBuilder


# logging.basicConfig(level=logging.info)

# Initialize application
app = FastAPI()

# Initialize agent
agent = ScanSheetAgent(api_key="api_key_xxxx", model="gpt-4")
prompt_builder = PromptBuilder(templates_dir="templates")

@app.post("/process-image")
async def process_image(image_bytes: str = (...)):
    try:
        variables = {
            "image_url": image_bytes
        }

        # Build the prompt
        prompt = prompt_builder.create_prompt(
            user_template="USER.txt",
            system_template="SYSTEM.txt",
            variables=variables
        )

        response = agent.run(prompt=prompt)   # json object
        return JSONResponse(content={ "table": response })

    except Exception as e:  # agent error
        return JSONResponse(content={ "error": str(e) }, status_code=500)