from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import RedirectResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
# import json
# import logging
from scansheet_agent import ScanSheetAgent, PromptBuilder

# logging.basicConfig(level=logging.info)

# Initialize application
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allows all (not secure)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent
agent = ScanSheetAgent(api_key="api_key_xxxx", model="gpt-4")
prompt_builder = PromptBuilder(templates_dir="templates")

@app.post("/process-image")
async def process_image(request: Request):
    try:
        data = await request.json()
        image_bytes = data.get("image_bytes")

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
        print(response)
        return JSONResponse(content={ "table": response })

    except Exception as e:  # agent error
        print("error")
        return JSONResponse(content={ "error": str(e) }, status_code=500)