#!/usr/bin/python
#!/usr/bin/env python # -*- coding: UTF-8 -*-
# Main.py

import cgi


import MySQLdb
import cv2
import numpy as np
import os

import DetectChars
import DetectPlates
import PossiblePlate


import os

DB_HOST = '52.38.138.57'
DB_USER = 'remote'
DB_PASS = '1234'
DB_NAME = 'bd_banners'

# module level variables ##########################################################################
SCALAR_BLACK = (0.0, 0.0, 0.0)
SCALAR_WHITE = (255.0, 255.0, 255.0)
SCALAR_YELLOW = (0.0, 255.0, 255.0)
SCALAR_GREEN = (0.0, 255.0, 0.0)
SCALAR_RED = (0.0, 0.0, 255.0)

showSteps = False
showStepsSegmentacion = False
showSteps1 = False
showSteps2 = False


def run_query(query=''):
    datos = [DB_HOST, DB_USER, DB_PASS, DB_NAME]

    conn = MySQLdb.connect(*datos)  # Conectar a la base de datos
    cursor = conn.cursor()  # Crear un cursor
    cursor.execute(query)  # Ejecutar una consulta

    if query.upper().startswith('SELECT'):
        data = cursor.fetchall()  # Traer los resultados de un select

    else:
        conn.commit()  # Hacer efectiva la escritura de datos
        data = None

    cursor.close()  # Cerrar el cursor
    conn.close()  # Cerrar la conexión

    return data




###################################################################################################
def main():

    blnKNNTrainingSuccessful = DetectChars.loadKNNDataAndTrainKNN()         # attempt KNN training

    if blnKNNTrainingSuccessful == False:                               #
        print "\nerror: KNN traning was not successful\n"
        return


    #Tk().withdraw()
    #filename = askopenfilename()
    #print(filename)

    #fullpathimg = os.path.abspath(result)

    #print (fullpathimg)


    #res = cv2.imread(fileimg)  # open image

    #res = cv2.imread("c8.jpg")  # open image

    while True:
        query = "SELECT tipo_imagen FROM imagenes "
        datos = [DB_HOST, DB_USER, DB_PASS, DB_NAME]

        conn = MySQLdb.connect(*datos)  # Conectar a la base de datos
        cursor = conn.cursor()  # Crear un cursor
        cursor.execute(query)  # Ejecutar una consulta
        #result = run_query(query)
        #data= cursor.fetchone()
        #result = str(cursor.fetchone()[0])
        result = cursor.fetchall()
        cursor.close()  # Cerrar el cursor
        conn.close()

        for list in result:
            for x in list:
                print os.path.abspath(x)
                fileimg = os.path.abspath(x)
                res = cv2.imread(fileimg)  # open image
                height, width, channels = res.shape
                print height, width, channels

                # print  result
                imgOriginalScene = np.mat
                if height > 650 or width > 1000:
                    print "Nuevo size imagen!"
                    imgOriginalScene = cv2.resize(res, (1000, 650))
                else:
                    print "NO editado size"
                    imgOriginalScene = res

                if imgOriginalScene is None:
                    print "\nError: imagen no encontrada \n\n"
                    os.system("pause")
                    return
                    # end if


                listOfPossiblePlates = DetectPlates.detectPlatesInScene(imgOriginalScene)           # detecta matriculas

                listOfPossiblePlates = DetectChars.detectCharsInPlates(listOfPossiblePlates)        # detect chars in plates

               # cv2.imshow("imgOriginal", imgOriginalScene)            # imagenOriginal

                if len(listOfPossiblePlates) == 0:
                    print "\nno license plates were detected\n"
                else:
                    listOfPossiblePlates.sort(key = lambda possiblePlate: len(possiblePlate.strChars), reverse = True)



                licPlate = listOfPossiblePlates[0]

                #cv2.imshow("Matricula", licPlate.imgPlate)           # Imagen solo la matricula
                #cv2.imwrite("imgPlate.png", licPlate.imgPlate)


                if len(licPlate.strChars) == 0:
                    print "\nNigun caracter encontrado\n\n"
                    return

                drawRedRectangleAroundPlate(imgOriginalScene, licPlate)             # delimita placa

                print "\nlicense plate read from image = " + licPlate.strChars + "\n"       # write license plate text to std out
                print "----------------------------------------"

                writeLicensePlateCharsOnImage(imgOriginalScene, licPlate)

                #cv2.imshow("imgOriginalMatricula", imgOriginalScene)

                #cv2.imwrite("imgOriginalScene.png", imgOriginalScene)

                conn = MySQLdb.connect(*datos)  # Conectar a la base de datos
                cursor = conn.cursor()  # Crear un cursor

                try:
                    cursor.execute("""INSERT INTO imgplaca (pathImg, placa) values (%s, %s)""", (fileimg, licPlate.strChars))
                    conn.commit()
                except:
                    print "error mysql"
                    conn.rollback()

                conn.close()

            #cv2.waitKey(0)

    return
# end main

###################################################################################################
def drawRedRectangleAroundPlate(imgOriginalScene, licPlate):

    p2fRectPoints = cv2.boxPoints(licPlate.rrLocationOfPlateInScene)            # vertices de la placa

    cv2.line(imgOriginalScene, tuple(p2fRectPoints[0]), tuple(p2fRectPoints[1]), SCALAR_RED, 2)         #lineas que rodean la placa
    cv2.line(imgOriginalScene, tuple(p2fRectPoints[1]), tuple(p2fRectPoints[2]), SCALAR_RED, 2)
    cv2.line(imgOriginalScene, tuple(p2fRectPoints[2]), tuple(p2fRectPoints[3]), SCALAR_RED, 2)
    cv2.line(imgOriginalScene, tuple(p2fRectPoints[3]), tuple(p2fRectPoints[0]), SCALAR_RED, 2)
# end function

###################################################################################################

def writeLicensePlateCharsOnImage(imgOriginalScene, licPlate):
    ptCenterOfTextAreaX = 0                             # this will be the center of the area the text will be written to
    ptCenterOfTextAreaY = 0

    ptLowerLeftTextOriginX = 0                          # this will be the bottom left of the area that the text will be written to
    ptLowerLeftTextOriginY = 0

    sceneHeight, sceneWidth, sceneNumChannels = imgOriginalScene.shape
    plateHeight, plateWidth, plateNumChannels = licPlate.imgPlate.shape

    intFontFace = cv2.FONT_HERSHEY_SIMPLEX                      # choose a plain jane font
    fltFontScale = float(plateHeight) / 30.0                    # base font scale on height of plate area
    intFontThickness = int(round(fltFontScale * 1.5))           # base font thickness on font scale

    textSize, baseline = cv2.getTextSize(licPlate.strChars, intFontFace, fltFontScale, intFontThickness)        # call getTextSize

            # unpack roatated rect into center point, width and height, and angle
    ( (intPlateCenterX, intPlateCenterY), (intPlateWidth, intPlateHeight), fltCorrectionAngleInDeg ) = licPlate.rrLocationOfPlateInScene

    intPlateCenterX = int(intPlateCenterX)              # make sure center is an integer
    intPlateCenterY = int(intPlateCenterY)

    ptCenterOfTextAreaX = int(intPlateCenterX)         # the horizontal location of the text area is the same as the plate

    if intPlateCenterY < (sceneHeight * 0.75):                                                  # if the license plate is in the upper 3/4 of the image
        ptCenterOfTextAreaY = int(round(intPlateCenterY)) + int(round(plateHeight * 1.6))      # write the chars in below the plate
    else:                                                                                       # else if the license plate is in the lower 1/4 of the image
        ptCenterOfTextAreaY = int(round(intPlateCenterY)) - int(round(plateHeight * 1.6))      # write the chars in above the plate
    # end if

    textSizeWidth, textSizeHeight = textSize                # unpack text size width and height

    ptLowerLeftTextOriginX = int(ptCenterOfTextAreaX - (textSizeWidth / 2))           # calculate the lower left origin of the text area
    ptLowerLeftTextOriginY = int(ptCenterOfTextAreaY + (textSizeHeight / 2))          # based on the text area center, width, and height

            # write the text on the image
    cv2.putText(imgOriginalScene, licPlate.strChars, (ptLowerLeftTextOriginX, ptLowerLeftTextOriginY), intFontFace, fltFontScale, SCALAR_YELLOW, intFontThickness)
# end function

###################################################################################################
if __name__ == "__main__":
    main()
