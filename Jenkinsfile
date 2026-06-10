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


    triggers {
        pollSCM('H 5 * * *') // Polls daily at 5 AM
    }

    stages{
        stage('Verify Python') {
            steps {
                sh 'python3 --version'
                sh 'which python3'
                sh 'pip3 --version'
            }
        }

         stage('Checkout Code') {
             steps {
                 // Use Jenkins' built-in Git step
                 git url: 'git@github.com:yuanDataScience/dvc_pipeline.git',
                 credentialsId: 'github_ssh',
                 branch: 'main'
             }
         }

//         stage('Verify MinIO Credentials (Env)') {
//             steps {
//                 sh '''
//                     [ -n "$AWS_ACCESS_KEY_ID" ] || exit 1
//                     [ -n "$AWS_SECRET_ACCESS_KEY" ] || exit 1
//                     echo "MinIO credentials present"
//                 '''
//             }
//         }
//
//         stage('Verify MinIO Access (mc)') {
//             steps {
//                 sh '''
//                     mc alias set minio http://minio.mlops.svc.cluster.local:9000 \
//                         "$AWS_ACCESS_KEY_ID" "$AWS_SECRET_ACCESS_KEY"
//
//                     echo "MinIO buckets:"
//                     mc ls minio
//                 '''
//             }
//         }


stage('Verify DVC Configuration') {
            steps {
                sh '''
                    dvc --version
                    dvc root
                    dvc remote list
                    dvc remote default
                    echo "DVC configuration valid"
                '''
            }
        }

stage('Verify DVC Access to MinIO') {
    steps {
        sh '''
            echo "Checking DVC ↔ MinIO connectivity (read-only)"
            dvc status -c
            echo "DVC remote is reachable"
        '''
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



        stage('Run Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    which pytest
                    export PYTHONPATH=$(pwd)
                    pytest
                '''
            }
        }

        stage('Git Push Test') {
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
