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
                 sshagent(credentials: ['github_ssh']) {
                     sh '''
                     set -e

                mkdir -p ~/.ssh
                ssh-keyscan github.com >> ~/.ssh/known_hosts

                git clone git@github.com:yuanDataScience/ci_pipeline.git
                cd ci_pipeline
                '''
                 }

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


        stage('Prepare directories') {
            steps {
                sh 'mkdir -p data/processed_dataset'
                sh 'mkdir -p data/raw_dataset'
            }
        }


        stage('preprocess data') {
            steps {
                sh '''
                    . venv/bin/activate
                    python3 src/utils.py
                    python3 src/process_dataset.py
                    python3 -m pip install --upgrade pip
                '''
            }
        }

        stage('update git and dvc') {
            steps {
                dir('ci_pipeline') {
                sh '''

                    git config user.name "jenkins"
                    git config user.email "jenkins@ci.local"

                    dvc add data/raw_dataset/train.csv
                    dvc add data/raw_dataset/test.csv
                    dvc add data/processed_dataset/train.csv
                    dvc add data/processed_dataset/test.csv

                    git add data/raw_dataset/*.dvc
                    git add data/processed_dataset/*.dvc
                    git add .gitignore

                    git commit -m "Update datasets via DVC" || echo "No changes to commit"

                    dvc push
                    git push origin HEAD
                '''
                }
            }

        }

        stage('Extract Git Metadata') {
            steps {
                dir('ci_pipeline') {
                    script {
                        env.GIT_SHA = sh(script: "git rev-parse HEAD", returnStdout: true).trim()
                        env.GIT_BRANCH = sh(script: "git rev-parse --abbrev-ref HEAD", returnStdout: true).trim()
                        env.SHORT_SHA = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    }
                }
            }
        }


        stage('train model') {
//              environment {
//                 //extract the first 7 characters of the Git Commit Hash
//                 // Fall back to 'latest' if GIT_COMMIT isn't populated for some reason
//
//                 SHORT_SHA = "${env.GIT_COMMIT ? env.GIT_COMMIT.take(7) : 'latest'}"
//             }
            steps {
                sh '''
                    . venv/bin/activate
                    python3 src/train.py \
                    --sha_id ${SHORT_SHA} \
                    --git_sha ${GIT_SHA} \
                    --git_branch ${GIT_BRANCH}

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
