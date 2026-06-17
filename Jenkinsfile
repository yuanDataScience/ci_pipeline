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
    - name: kaniko
      image: gcr.io/kaniko-project/executor:debug
      command: ["cat"]
      tty: true
      volumeMounts:
      - name: registry-credentials
        mountPath: /kaniko/.docker # Kaniko automatically looks here for config.json
  volumes:
  - name: dvc-cache-volume
    persistentVolumeClaim:
      claimName: jenkins-dvc-cache-pvc
  - name: registry-credentials
    secret:
      secretName: regcred
      items:
      - key: .dockerconfigjson
        path: config.json
"""
  }
}

    environment {
            VENV_DIR = 'venv'
        }

    stages{
        stage('Checkout Code') {
            steps {
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
                dir('ci_pipeline') {
                sh '''
                    python3 -m venv $VENV_DIR
                    . $VENV_DIR/bin/activate
                   pip install -r requirements.txt
                '''
                }
            }
        }

        stage('Prepare directories') {
            steps {
                dir('ci_pipeline') {
                sh '''
                mkdir -p data/processed_dataset
                mkdir -p data/raw_dataset
                '''
                }
            }
        }

        stage('DVC Setup') {
            steps {
                // Configure DVC to use the shared persistent cache directory
                sh 'dvc config cache.dir /var/jenkins_dvc_cache'
                sh 'dvc config cache.shared group'

                // Use copy for guaranteed Samba compatibility, or hardlink,copy as a fallback
                sh 'dvc config cache.type copy' // or copy, depending on your storage backend
            }
        }


        stage('load training data') {
            steps {
                dir('ci_pipeline') {
                sh '''
                    . venv/bin/activate
                    python3 src/utils.py

                    echo "After dataset creation:"
                    pwd
                    find . -name train.csv
                '''
                }
            }
        }

        stage('preprocess data') {
            steps {
                dir('ci_pipeline'){
                sh '''
                    . venv/bin/activate
                    python3 src/process_dataset.py
                '''
                }
            }
        }

        stage('update git and dvc') {
            steps {
                dir('ci_pipeline') {

                    sshagent(credentials: ['github_ssh']) {
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
            steps {
                dir('ci_pipeline') {
                sh '''
                    . venv/bin/activate
                    python3 src/train.py \
                    --sha_id ${SHORT_SHA} \
                    --git_sha ${GIT_SHA} \
                    --git_branch ${GIT_BRANCH}

                '''
                }
            }
        }

        stage('build docker') {

            steps {
                sshagent(credentials: ['github_ssh']) {
                    sh '''
                    rm -rf inference_fastapi_k8s
                    git clone git@github.com:yuanDataScience/inference_fastapi_k8s.git
                    '''
                 }
                dir('inference_fastapi_k8s') {
                    container('kaniko') {
                    // Back to a clean, one-line command
                     sh "echo BUILDING IMAGE WITH TAG: ${env.SHORT_SHA}"

                    sh """
                    /kaniko/executor \
                    --context=. \
                    --dockerfile=Dockerfile \
                    --destination=huangyuan2000/fastapi-demo:${env.SHORT_SHA} \
                    --cache=true \
                    --cache-dir=/var/jenkins_dvc_cache \
                    --no-push-cache=true
                    """
                    }

                }
            }
        }

        stage('Git update deployment') {
            steps {
                sshagent(credentials: ['github_ssh']) {
                sh '''
                set -e

                mkdir -p ~/.ssh
                ssh-keyscan github.com >> ~/.ssh/known_hosts

                rm -rf argocd_ci
                git clone git@github.com:yuanDataScience/argocd_ci.git
                cd argocd_ci

                git config user.name "jenkins"
                git config user.email "jenkins@ci.local"

                # if kustomize binary is available in the image, use it
                if command -v kustomize &> /dev/null; then
                        kustomize edit set image huangyuan2000/fastapi-demo=huangyuan2000/fastapi-demo:${SHORT_SHA}
                    else
                        # Fallback parsing block using sed if kustomize isn't installed in the runner
                        if grep -q "newTag:" kustomization.yaml; then
                            sed -i "s/newTag:.*/newTag: ${SHORT_SHA}/g" kustomization.yaml
                        else
                            echo -e "\\n  newTag: ${SHORT_SHA}" >> kustomization.yaml
                        fi
                    fi

                    git add kustomization.yaml
                    git commit -m "Auto-bump inference image tag to ${SHORT_SHA} [skip ci]" || echo "No changes to commit"


                git push origin main
                '''
                }

            }
        }
    }
}
