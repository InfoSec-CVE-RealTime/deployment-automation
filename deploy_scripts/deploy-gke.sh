gcloud config set project bda-project-05012023
gcloud container clusters create-auto bda-cluster --region=us-west1
gcloud container clusters get-credentials bda-cluster --region=us-west1