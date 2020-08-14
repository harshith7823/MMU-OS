import multiprocessing as mp
import os
import random
from collections import deque


with open("config_mmu.txt") as a:
        fp=a.read()
        inp=fp.split("\n")
config_mmu=[]
for i in inp:
    s=""+i
    aa=s.split("=")
    config_mmu.append(aa[1])

def MMU(page_request,V,C,tlb_a_q,tlb_miss_q,fault_q):
    global config_mmu
    TLB=[]
    main_mem=[]
    main_mem_size=int(config_mmu[0])
    main_mem_access_time=int(config_mmu[1])
    disk_access_time=int(config_mmu[2])   
    TLB_size=int(config_mmu[3])
    TLB_access_time=int(config_mmu[4])

    v=V.recv()
    page_table=[[i,0] for i in range(v)]
    c=C.get()

    TLB_miss=0
    mem_access_time=0
    page_fault=0
    
    #MMU opearation --->
    
    for i in range(c):
        #print()
        virtual_page_no=page_request.get()
        flag=False
        mem_access_time+=TLB_access_time
        # print("mmm",virtual_page_no)
        if virtual_page_no in TLB:
            #print("***** TLB HIt ******")
            #print("VPage :",virtual_page_no,"TLB -->",TLB)
            mem_access_time+=main_mem_access_time 
        else:
            #print("-----TLB miss ----")
            #print("VPage :",virtual_page_no,"TLB -->",TLB)
            TLB_miss+=1
            mem_access_time+=main_mem_access_time #accessing page_table 
            if page_table[virtual_page_no][1]==1:
                #print("Found in memory :",page_table)
                mem_access_time+=main_mem_access_time # accessing the page
                if len(TLB)==TLB_size:
                    del(TLB[0])
                    TLB.append(virtual_page_no)
                else:
                    if virtual_page_no in TLB:
                        TLB.remove(virtual_page_no)
                    TLB.append(virtual_page_no)
            else:
                #print("--@@--fectching from disk--@@--")
                page_fault+=1
                mem_access_time+=disk_access_time
                ''' upadate_main_mem '''
                if len(main_mem)==main_mem_size:
                    flag=True
                    temp=main_mem[0]
                    del(main_mem[0])
                    main_mem.append(virtual_page_no)
                else:
                    if virtual_page_no in main_mem:
                        main_mem.remove(virtual_page_no)
                    main_mem.append(virtual_page_no)
                ''' upadate TLB'''
                if len(TLB)==TLB_size:
                    del(TLB[0])
                    TLB.append(virtual_page_no)
                else:
                    if virtual_page_no in TLB:
                        TLB.remove(virtual_page_no)
                    TLB.append(virtual_page_no)
                ''' upadate page_table'''
                for i,j in enumerate(page_table):
                    if j[0]==virtual_page_no:
                        page_table[i][1]=1
                    if flag and j[0]==temp:
                        page_table[i][1]=0
    #print("Tota access time :",mem_access_time,"sec")
    tlb_a_q.put(mem_access_time)
    tlb_miss_q.put(TLB_miss)
    fault_q.put(page_fault)
    #print("TLB miss count   :",TLB_miss)
    #print("Flushing")
    #print()

#process defination --->
    
def proc_def(Q,Nq,Vq,page_request):
    c=Q.get()
    v=Vq.get()
    N=Nq.get()
    page_requests=[random.randint(0,v-1) for i in range(N)]
    for i in page_requests:
        page_request.put(i)
    #print("V:",v,"N:",N)
    
    
    
if __name__=="__main__":
    lock =mp.Lock()
    Q=mp.Queue()
    C=mp.Queue()
    Nq=mp.Queue()
    Vq=mp.Queue()
    P,V=mp.Pipe()

    tlb_a_q=mp.Queue()
    tlb_miss_q=mp.Queue()
    fault_q=mp.Queue()
    
    page_request=mp.Queue()
    proc=[]
    with open("config.txt","r") as a:
        fp=a.read()
        inp=fp.split("\n")

    process=[] # holds details of each process 

    for i in inp:
        s=" "+i
        sp=s.split(",")
        l=[]
        for j in sp:
            l.append(j)
        process.append(l)
    proc_time=[]
    for i in process:
        proc_time.append(0)

    proc_miss=[]
    for i in process:
        proc_miss.append(0)
    fault=[]
    for i in process:
        fault.append(0)
    p_original=[]
    for i in process:
        p_original.append(i[2])

    #Scheduler function ---> 
    def scheduler():
        global process
        a=open("config_sch.txt","r")
        fp=a.read()
        x=fp.split("=")
        queue=deque(process)
        c=int(x[1])
        while(1):
            Q.put(c)
            if(len(queue)==0):
                break
            l=queue.popleft()
            ind=int(l[3])
            val=int(l[2])
    
            #print("Scheduling Process[",ind,"]",l)
            
            val=int(l[2])
            a=int(l[1])
                    
            Vq.put(a)
            if(val>=c):
                val-=c
                l[2]=val
                Nq.put(c)
                C.put(c)
            elif(val<c):
                Nq.put(val)
                C.put(val)
                l[2]=0
            
            
            mmu=mp.Process(target=MMU,args=(page_request,V,C,tlb_a_q,tlb_miss_q,fault_q))
            mmu.start()
            P.send(a)
            p=mp.Process(target=proc_def,args=(Q,Nq,Vq,page_request))
            p.start()
            tlb_miss=tlb_miss_q.get()
            tlb_time=tlb_a_q.get()
            f=fault_q.get()
            proc_time[ind]+=tlb_time
            proc_miss[ind]+=tlb_miss
            fault[ind]+=f
            p.join()
            mmu.join()
            
            if(val>0):
                queue.append(l)
            


    scheduler()
    j=0
    print()
    print("----Memory access times----")
    for i in proc_time:
        j=j+1
        print("Process",j," Memory access time :",i)
    print("----Total page miss (faults)----")
    j=0
    for i in proc_miss:
        j=j+1
        print("Process",j," Miss rate:",i)

    print("----Page Fault rates----")
    l=len(p_original)
    for i in range(0,l):
        div=(int(fault[i])/int(p_original[i]))*100
        print("Process[",i,"] page fault rate:",div)
 
