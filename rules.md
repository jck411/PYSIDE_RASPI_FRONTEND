Always prefer simple solutions  
– try to fix things at the cause, not the symptom.
– do only what you are asked, make suggestions for enhancements 
– Use event  driven mechanisms whenever possible
– Always use asynch methods unless it doesn't give significant advantage
– Avoid duplication of code whenever possible, which means checking for other areas of the codebase that might already have similar code and functionality  
– You are careful to only make changes that are requested or you are confident are well understood and related to the change being requested  
– When fixing an issue or bug, do not introduce a new pattern or technology without first exhausting all options for the existing implementation. And if you finally do this, make sure to remove the old implementation afterwards so we don’t have duplicate logic.  
– Keep the codebase very clean and organized  
– Avoid writing scripts in files if possible, especially if the script is likely only to be run once  
– Avoid having files over 200–300 lines of code. Refactor at that point.  
– Mocking data is only needed for tests, never mock data for dev or prod  
– Never add stubbing or fake data patterns to code that affects the dev or prod environments  
– Never overwrite my .env file without first asking and confirming
-- pdate/home/jack/PYSIDE_RASPI_FRONTEND/ARCHITECTURE.md after making changes