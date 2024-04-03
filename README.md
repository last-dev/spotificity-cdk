# SpotificityCDK

AWS CDK code that spins up the cloud infra for my 'spotificity-cli' crud app.

## **Deployment**

If I want to deploy to my desired account, I can run my deployment bash script. 

- Activate virtual environment inside project directory: `source .venv/bin/activate`
- Install the required dependencies: `pip install -r requirements.txt`
- Make desired code changes
- Deploy to my desired Spotificity account based on stage:
   1. Change to project root directory
   2. Run deployment script while passing in the AWS CLI profile I want to use:

      ```bash
      ./deploy.sh -p [profile_name]
      ```
