from tkinter import *
from tkinter import font
import pandas as pd

class MyWindow:
    def __init__(self, win):
        #introducing the data 
        self.lbtitulo=Label(win, text='Diseño de tuberias secundaria',font=25)
        self.lbQ=Label(win, text='Caudal (m3/h)')
        self.lbS=Label(win, text='Espaciamiento entre salidas')
        self.lbL=Label(win, text='Largo de tubería (m)')
        self.lbHF=Label(win, text='Pérdidas por fricción disponibles (m)')
        self.tQ=Entry()
        self.tS=Entry()
        self.tL=Entry()
        self.tHF=Entry()
        
        self.lbtitulo.place(x= 25, y=10)
        self.lbQ.place(x=50, y=50)
        self.tQ.place(x=300, y=50)
        self.lbS.place(x=50, y=75)
        self.tS.place(x=300, y=75)
        self.lbL.place(x=50, y=100)
        self.tL.place(x=300, y=100)
        self.lbHF.place(x=50, y=125)
        self.tHF.place(x=300, y=125)
        self.btn1 = Button(win, text='Calculate')
        self.b1=Button(win, text='Calculate', command=self.Calculate)
        self.b1.place(x=300, y=150)

        #DATOS DE SALIDA 
        self.lbtitulo=Label(win, text='Solución con un diámetro',font=15)
        self.lbDia=Label(win, text='Diamétro interno sugerido (mm)')
        self.lbHF1=Label(win, text='Pérdidas por fricción calculadas (m)')
        self.lbVel=Label(win, text='La Velocidad en tubo (m/s)')
        self.lbt_avance=Label(win, text='Tiempo de avance (min)')
        self.tDia=Entry()
        self.tHF1=Entry()
        self.tVel=Entry()
        self.tt_avance=Entry()
        self.lbtitulo.place(x= 25, y=190)
        self.lbDia.place(x=50, y=225)
        self.tDia.place(x=300, y=225)
        self.lbHF1.place(x=50, y=250)
        self.tHF1.place(x=300, y=250)
        self.lbVel.place(x=50, y=275)
        self.tVel.place(x=300, y=275)
        self.lbt_avance.place(x=50, y=300)
        self.tt_avance.place(x=300, y=300)

        #DATOS DE SALIDA DIAMETRO COMBINADO
        self.lbtitulo=Label(win, text='Solución con dos diámetros',font=15)
        self.lbDia1=Label(win, text=' Primer diámetro / Largo')
        self.lbDia2=Label(win, text=' Segundo diámetro / Largo')
        self.lbHFC=Label(win, text='Pérdidas por fricción calculadas (m)')
        self.lbVelC=Label(win, text='Velocidad del tubo (m/s)')
        self.lbt_avanceC=Label(win, text='Tiempo de avance (min)')
        self.tDia1=Entry()
        self.tDia2=Entry()
        self.tHFC=Entry()
        self.tVelC=Entry()
        self.tt_avanceC=Entry()
        self.lbtitulo.place(x= 25, y=340)
        self.lbDia1.place(x=50, y=375)
        self.lbDia2.place(x=50, y=400)
        self.tDia1.place(x=300, y=375)
        self.tDia2.place(x=300, y=400)
        self.lbHFC.place(x=50, y=425)
        self.tHFC.place(x=300, y=425)
        self.lbVelC.place(x=50, y=450)
        self.tVelC.place(x=300, y=450, width=250)
        self.lbt_avanceC.place(x=50, y=475)
        self.tt_avanceC.place(x=300, y=475)
 
        self.lbtitulo=Label(win, text='Prof. Gregory Guevara')
        self.lbtitulo.place(x= 300, y=525)
        self.lbtitulo=Label(win, text='Riego & Drenaje / Universidad EARTH')
        self.lbtitulo.place(x= 300, y=550)
        self.lbtitulo=Label(win, text='Nota:los díametro en PVC SDR 41')
        self.lbtitulo.place(x= 370, y=150)
        
    def Calculate(self):
        self.tDia.delete(0, 'end')
        self.tHF1.delete(0, 'end')
        self.tVel.delete(0, 'end')
        self.tt_avance.delete(0, 'end')
        self.tDia1.delete(0, 'end')
        self.tDia2.delete(0, 'end')
        self.tHFC.delete(0, 'end')
        self.tVelC.delete(0, 'end')
        self.tt_avanceC.delete(0, 'end')
        Q=float(self.tQ.get())
        S=float(self.tS.get())
        L=float(self.tL.get())
        HF=float(self.tHF.get())     
        # seleccion de diametros correctos
        C= 150 #rugosidad  
        Salidas=L/S #definimos la cantidad de salidas que tiene el lateral de riego
        F=2*Salidas/(2*Salidas-1)*((1/2.852)+0.852**0.5/(6*Salidas**2)) #Factor de Cristiansen para la ecuación de HW
        Q_salida=Q/Salidas
        dia=[39.8,45.9,57.38,84.58,108.72,160.08,208.42,259.75,308.05,369.7] #Tuberia SDR 41 diametro interno
        LL=L # de longitud total fija
        LLL=0 #longitud 2 del diametro combinado
        n=-1 #punto de inicio para el loop que busca el diametro inferior
        HF3=HF #valor de inicio para la combinacion de diametros 
        for j in dia: #codigo de para calcular el diametro correcto
            HF1= (1.131*10**9*(Q/C)**1.852*L*j**-4.872*F)
            if j==39.8: #definimos el diametro inferior
                jj=0
            else: #loop del diametro inferior que viene detras del diametro que se calcula
                n+=1
                jj=dia[n]    
            Area= 3.141516*(j/2000)**2
            Vel=Q/Area/3600    
            #definimos el diametro inferior
            if Vel>3: # prueba para evitar velocidades turbulentas 
                continue   
            if HF1<HF:  #Prueba para saber que es el díametro correcto
                while HF3 >= HF:  #si el diametro es el correcto hace loop para ajustar L combinación de diametros
                    L-=S
                    LLL=LL-L
                    Salida1=L/S
                    Salida2=LLL/S
                    F1=2*Salida1/(2*Salida1-1)*((1/2.852)+(0.852**0.5)/(6*Salida1**2))
                    F2=2*Salida2/(2*Salida2-1)*((1/2.852)+(0.852**0.5)/(6*Salida2**2))
                    Area2= 3.141516*(jj/2000)**2
                    Q2=Q*L/LL #proporcion del caudal que pasasá por el diametro menor
                    Vel2=Q2/Area2/3600 #velocidad del diametro menor
                    HF3=(1.131*10**9*(Q2/C)**1.852*L*jj**-4.872*F1)+(1.131*10**9*(Q/C)**1.852*LLL*j**-4.872*F2 )
                break
        #tiempos de avance 
        df=pd.DataFrame()
        df["salidas"]=0
        df["long_acum"]=0
        df["q_tramo"]=0
        df["v_tramo"]=0
        df["t_tramo"]=0
        df["t_tramo_acum"]=0
        df["v_tramo_comb"]=0
        df["t_tramo_comb"]=0

        a=range(1,int(Salidas)+1)
        qq=Q+Q_salida
        ss=0
        for x in a: 
            qq=qq-Q_salida # en este vamos restado el caudal total cada vez que pasamos por una salida 
            ss=ss+S #step para el número de salidas 
            df.at[x,'salidas']=j # determinación de la columna "longitud acumulada"
            df.at[x,'long_acum']=ss # determinación de la columna "longitud acumulada"
            df.at[x,'q_tramo']=qq

       #calculos del tiempo de avance sin combinación de diametros  
        df["v_tramo"]=df["q_tramo"]/Area/3600
        df["t_tramo"]=S/df["v_tramo"]
        df["t_tramo_acum"]=df['t_tramo'].cumsum()/60
        t_avance= round(df["t_tramo"].sum()/60,2)


        #calculo del tiempo de avance con combinación de diametros 
        for x in a:
            longitud=(df.loc[x,'long_acum'])
            if longitud<LLL:
                df.at[x,'v_tramo_comb']=df.loc[x,'v_tramo']
            else:
                df.at[x,'v_tramo_comb']=df.loc[x,'q_tramo']/Area2/3600 
        df["t_tramo_comb"]=S/df["v_tramo_comb"]
        df["t_tramo_comb_acum"]=df['t_tramo_comb'].cumsum()/60

        t_avance_comb= round(df["t_tramo_comb"].sum()/60,2)
    
        #Salidas sin combinación   
        HF1=round(HF1,2)
        HF3=round(HF3,2)
        L=round(L,2)
        LL=round(LL,2) 
        LLL=round(LLL,2)
        Vel=round(Vel,2)
        Vel2=round(Vel2,2)  
        self.tDia.insert(END, str(j))
        self.tHF1.insert(END, str(HF1))
        self.tVel.insert(END, str(Vel))
        self.tt_avance.insert(END, str(t_avance))
        self.tDia1.insert(END, str(j)+" mm x "+str(LLL)+" m")
        self.tDia2.insert(END, str(jj)+" mm x "+str(L)+" m")
        self.tHFC.insert(END, str(HF3))
        self.tVelC.insert(END, str(Vel)+" m/s x "+str(j)+" mm y " +str(Vel2)+" m/s x "+str(jj)+" mm")
        self.tt_avanceC.insert(END, str(t_avance_comb))




window=Tk()
mywin=MyWindow(window)
window.title('Diseño de tuberías secundarias')
window.geometry("600x600+5+5")
window.mainloop()

