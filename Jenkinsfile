pipeline {
    agent {
  kubernetes {
    namespace 'jenkins'
        defaultContainer 'python'
    yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: python
      image:  huangyuan2000/python-dvc:3.10.1
      command:
        - sleep
        - infinity
      env:
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: minio-credentials
              key: access_key
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: minio-credentials
              key: secret_key
      volumeMounts:
      - name: dvc-cache-volume
        mountPath: /var/jenkins_dvc_cache
  volumes:
  - name: dvc-cache-volume
    persistentVolumeClaim:
      claimName: jenkins-dvc-cache-pvc
"""
  }
}

    environment {
            VENV_DIR = 'venv'
        }


    stages{
        stage('Checkout Code') {
            steps {
                 // Use Jenkins' built-in Git step
                 git url: 'git@github.com:yuanDataScience/ci_pipeline.git',
                 credentialsId: 'github_ssh',
                 branch: 'main'
            }
         }


        stage('Setup Python Environment') {
            steps {
                sh '''

                    python3 -m venv $VENV_DIR
                    . $VENV_DIR/bin/activate

                   pip install -r requirements.txt
                '''
            }
        }


        stage('load training data') {
            steps {
                sh '''
                    . venv/bin/activate
                    python3 src/utils.py
                '''
            }
        }

        stage('preprocess data') {
            steps {
                sh '''
                    . venv/bin/activate
                    python3 src/process_dataset.py
                '''
            }
        }

        stage('update git and dvc') {
            dvc add data/raw_dataset/train.csv
            dvc add data/raw_dataset/test.csv
            dvc add data/processed_dataset/train.csv
            dvc add data/processed_dataset/test.csv

            git add data/raw_dataset/*.dvc
            git add data/processed_dataset/*.dvc
            git add .gitignore

            dvc push
            git push

        }

        stage('train model') {
            steps {
                sh '''
                    . venv/bin/activate
                    python3 src/train.py
                '''
            }
        }



        stage('Git update deployment') {
            steps {
                sshagent(credentials: ['github_ssh']) {
                sh '''
                set -e

                mkdir -p ~/.ssh
                ssh-keyscan github.com >> ~/.ssh/known_hosts

                git clone git@github.com:yuanDataScience/argocd_apps.git
                cd argocd_apps

                git config user.name "jenkins"
                git config user.email "jenkins@ci.local"

                mkdir -p test
                touch test/.gitkeep

                git add test/.gitkeep
                git diff --cached --quiet || git commit -m "Test: create folder from Jenkins"

                git push origin main

                '''
                }

            }
        }
    }
}
