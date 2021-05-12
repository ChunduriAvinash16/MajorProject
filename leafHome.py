from tkinter import *
from PIL import Image, ImageTk

import tkinter.messagebox
import tkinter.filedialog
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as font
from tkinter.filedialog import askopenfilename

def predict(fileName):
    filename=fileName
    import numpy as np
    import pandas as pd
    import os
    import string
    dataset = pd.read_csv("Flavia_features.csv")
    ds_path = "Leaves"
    img_files = os.listdir(ds_path)

    breakpoints = [1001,1059,1060,1122,1552,1616,1123,1194,1195,1267,1268,1323,1324,1385,1386,1437,1497,1551,1438,1496,2001,2050,2051,2113,2114,2165,2166,2230,2231,2290,2291,2346,2347,2423,2424,2485,2486,2546,2547,2612,2616,2675,3001,3055,3056,3110,3111,3175,3176,3229,3230,3281,3282,3334,3335,3389,3390,3446,3447,3510,3511,3563,3566,3621]
    target_list = []
    for file in img_files:
        
        target_num = int(file.split(".")[0])
        flag = 0
        i = 0 
        for i in range(0,len(breakpoints),2):
            if((target_num >= breakpoints[i]) and (target_num <= breakpoints[i+1])):
                flag = 1
                break
        if(flag==1):
            target = int((i/2))
            target_list.append(target)

    y = np.array(target_list)
    X = dataset.iloc[:,1:]
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state = 142)
    from sklearn.preprocessing import StandardScaler
    sc_X = StandardScaler()
    X_train = sc_X.fit_transform(X_train)
    X_test = sc_X.transform(X_test)

    from sklearn import svm
    clf = svm.SVC()
    clf.fit(X_train,y_train)

    from sklearn.model_selection import GridSearchCV

    parameters = [{'kernel': ['rbf'],
                   'gamma': [1e-4, 1e-3, 0.01, 0.1, 0.2, 0.5],
                   'C': [1, 10, 100, 1000]},
                  {'kernel': ['linear'], 'C': [1, 10, 100, 1000]}
                 ]

    svm_clf = GridSearchCV(svm.SVC(decision_function_shape='ovr'), parameters, cv=5)
    svm_clf.fit(X_train, y_train)

    means = svm_clf.cv_results_['mean_test_score']
    stds = svm_clf.cv_results_['std_test_score']
    for mean, std, params in zip(means, stds, svm_clf.cv_results_['params']):
        print("%0.3f (+/-%0.03f) for %r" % (mean, std * 2, params))

    from sklearn.decomposition import PCA

    pca = PCA()


    pca.fit(X)


    import matplotlib.pyplot as plt
    #%matplotlib inline

    var1=np.cumsum(np.round(pca.explained_variance_ratio_, decimals=4)*100)

    import os
    import cv2
    def bg_sub():
        test_img_path = filename
        main_img = cv2.imread(test_img_path)
        img = cv2.cvtColor(main_img, cv2.COLOR_BGR2RGB)
        resized_image = cv2.resize(img, (1600, 1200))
        size_y,size_x,_ = img.shape
        gs = cv2.cvtColor(resized_image,cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gs, (55,55),0)
        ret_otsu,im_bw_otsu = cv2.threshold(blur,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        kernel = np.ones((50,50),np.uint8)
        closing = cv2.morphologyEx(im_bw_otsu, cv2.MORPH_CLOSE, kernel)
        
        ret_image, contours, hierarchy = cv2.findContours(closing,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        
        contains = []
        y_ri,x_ri, _ = resized_image.shape
        for cc in contours:
            yn = cv2.pointPolygonTest(cc,(x_ri//2,y_ri//2),False)
            contains.append(yn)

        val = [contains.index(temp) for temp in contains if temp>0]
        index = val[0]
        
        black_img = np.empty([1200,1600,3],dtype=np.uint8)
        black_img.fill(0)
        
        cnt = contours[index]
        mask = cv2.drawContours(black_img, [cnt] , 0, (255,255,255), -1)
        
        maskedImg = cv2.bitwise_and(resized_image, mask)
        white_pix = [255,255,255]
        black_pix = [0,0,0]
        
        final_img = maskedImg
        h,w,channels = final_img.shape
        for x in range(0,w):
            for y in range(0,h):
                channels_xy = final_img[y,x]
                if all(channels_xy == black_pix):
                    final_img[y,x] = white_pix
        
        return final_img
    bg_rem_img = bg_sub()

    import mahotas as mt

    def feature_extract(img):
        names = ['area','perimeter','pysiological_length','pysiological_width','aspect_ratio','rectangularity','circularity', \
                 'mean_r','mean_g','mean_b','stddev_r','stddev_g','stddev_b', \
                 'contrast','correlation','inverse_difference_moments','entropy'
                ]
        df = pd.DataFrame([], columns=names)

        #Preprocessing
        gs = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gs, (25,25),0)
        ret_otsu,im_bw_otsu = cv2.threshold(blur,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        kernel = np.ones((50,50),np.uint8)
        closing = cv2.morphologyEx(im_bw_otsu, cv2.MORPH_CLOSE, kernel)

        #Shape features
        image, contours, _ = cv2.findContours(closing,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        cnt = contours[0]
        M = cv2.moments(cnt)
        area = cv2.contourArea(cnt)
        perimeter = cv2.arcLength(cnt,True)
        x,y,w,h = cv2.boundingRect(cnt)
        aspect_ratio = float(w)/h
        rectangularity = w*h/area
        circularity = ((perimeter)**2)/area

        #Color features
        red_channel = img[:,:,0]
        green_channel = img[:,:,1]
        blue_channel = img[:,:,2]
        blue_channel[blue_channel == 255] = 0
        green_channel[green_channel == 255] = 0
        red_channel[red_channel == 255] = 0

        red_mean = np.mean(red_channel)
        green_mean = np.mean(green_channel)
        blue_mean = np.mean(blue_channel)

        red_std = np.std(red_channel)
        green_std = np.std(green_channel)
        blue_std = np.std(blue_channel)

        #Texture features
        textures = mt.features.haralick(gs)
        ht_mean = textures.mean(axis=0)
        contrast = ht_mean[1]
        correlation = ht_mean[2]
        inverse_diff_moments = ht_mean[4]
        entropy = ht_mean[8]

        vector = [area,perimeter,w,h,aspect_ratio,rectangularity,circularity,\
                  red_mean,green_mean,blue_mean,red_std,green_std,blue_std,\
                  contrast,correlation,inverse_diff_moments,entropy
                 ]

        df_temp = pd.DataFrame([vector],columns=names)
        df = df.append(df_temp)
        
        return df

    features_of_img = feature_extract(bg_rem_img)
    scaled_features = sc_X.transform(features_of_img)
    print(scaled_features)
    # y_pred_mobile = svm_clf.predict(features_of_img)
    y_pred_mobile = svm_clf.predict(scaled_features)
    y_pred_mobile[0]

    common_names = ['Pubescent bamboo','Chinese horse chestnut','Anhui Barberry', \
                    'Chinese redbud','True indigo','Japanese maple','Nanmu',' Castor aralia', \
                    'Chinese cinnamon','Goldenrain tree','Big-fruited Holly','Japanese cheesewood', \
                    'Wintersweet','Camphortree','Japan Arrowwood','Sweet osmanthus','Deodar','Ginkgo, Maidenhair tree', \
                    'Crape myrtle, Crepe myrtle','Oleander','Yew plum pine','Japanese Flowering Cherry','Glossy Privet',\
                    'Chinese Toon','Peach','Ford Woodlotus','Trident maple','Beales barberry','Southern magnolia',\
                    'Canadian poplar','Chinese tulip tree','Tangerine'
                   ]
    common_names[y_pred_mobile[0]]
    
    result= str(common_names[y_pred_mobile[0]])

    def remedi():
        
        filenamee='Remidies/'+result+".txt"
        print(filenamee)
        
        f = open(filenamee, "r")
        #print(f.read())
        
        root1 = tkinter.Toplevel()
        root1.geometry('700x400')
        lb1 = Label(root1, text=f.read(),font=('Times',18,'normal'),justify='left',fg="BLUE")
        lb1.place(x=75, y=50)
        

        root1.mainloop()
        

    
        
        
    
    root = tkinter.Toplevel()  
    canvas = Canvas(root, width = 400, height = 500)  
    canvas.pack()
    image=Image.open(filename)
    image=image.resize((300,300))

    lb1 = Label(root, text=result,font=('Times',15,'bold'),justify='center',fg="BLUE")
    lb1.place(x=50, y=350)

    
    img = ImageTk.PhotoImage(image)  
    canvas.create_image(50, 20, anchor=NW, image=img)

    btn1 = Button(root, text="View Remedies",  height=1,fg="black",font=('Times',20,'bold'),bg="SKYBLUE",justify='center',command=remedi)
    btn1.place(x=75, y=400)
    
    root.mainloop()

def show():
   
    fileName = askopenfilename(title='Select image for analysis ',filetypes=[('image files', '.jpg')])                   
    predict(fileName)

     


    



    
    
window9 = Tk()
window9.geometry('1400x500')
image=Image.open('unnamed.png')
image=image.resize((700,500))
photo_image=ImageTk.PhotoImage(image)
label=Label(window9,image=photo_image)
label.place(x=350,y=100)

lb1 = Label(window9, text="Classification on Leaves Based on their Species using Machine Learning Technique"
,font=('Times',20,'bold'),justify='center',fg="BLUE")
lb1.place(x=200, y=70)


btn1 = Button(window9, text="PICK AN IMAGE", height=1,fg="black",font=('Times',20,'bold'),bg="SKYBLUE",justify='center',command=show)
btn1.place(x=550, y=350)


window9.mainloop()
