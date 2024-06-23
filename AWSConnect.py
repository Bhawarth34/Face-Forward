import boto3
from botocore.exceptions import ClientError
import os
import io
from PIL import Image
from time import sleep

bucket = boto3.resource('s3', region_name = "ap-south-1")
database = boto3.client('dynamodb', region_name="ap-south-1")
rekognition = boto3.client('rekognition', region_name='ap-south-1')

def find_face(filename, date=None):
    if(os.path.exists(filename)):
        try:
            image = Image.open(filename)
            stream = io.BytesIO()
            image.save(stream,format="JPEG")
            image_binary = stream.getvalue()
            
            response = rekognition.search_faces_by_image(CollectionId='student-face-data', Image={'Bytes':image_binary})
            print(response)
            found = False
            for match in response['FaceMatches']:
                print (match['Face']['FaceId'],match['Face']['Confidence'])
        
                face = database.query(TableName='Student-Data', IndexName='RecognitionId', ExpressionAttributeValues={':rid': {'S': match['Face']['FaceId']}}, KeyConditionExpression="RecognitionId = :rid")
                print(face)
                if 'Items' in face and face['Items'] != []:
                    print ("Found Person: ",face['Items'][0]['Name']['S'])
                    found = True
                    os.remove(filename)
                    return face['Items'][0]
                    

            if not found:
                print("Person cannot be recognized")
                os.remove(filename)
                return None

            sleep(3)
            os.remove(filename)
        
        except rekognition.exceptions.InvalidParameterException as e:
            print(e)
            return None

        except ClientError as e:
            print(e)
            return None

        return None

def add_student_data(name, uid, course, section, image, bucketname):
    path = os.path.join("./uploaded_image", image) 
    if(os.path.exists(path)):
        try:
            database.put_item(TableName = "Student-Data", Item={'Name':{'S':name},'UID':{'S':uid},'Course':{'S':course},'Section':{'S':section}, 'RecognitionId':{'S':"a"}})
            file = open(path,'rb')
            object = bucket.Object(bucketname,image)
            ret = object.put(Body=file, Metadata={"uid":uid})
            print(ret)

        except ClientError as e:
            print(e)
            return False
        return True

    return False
