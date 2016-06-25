#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Created on Wed May 11 10:35:43 2016
"""

import sys
import glob
import subprocess, os


def get_files(a_dir,filetype):
    os.chdir(a_dir)
    return glob.glob(filetype)
    
def invert(row):
    if '<=' in row:
        row=row.replace('<=','>')
    elif '>=' in row:
        row=row.replace('>=','<')
    elif '==' in row:
        row=row.replace('==','!=')
    elif '!=' in row:
        row=row.replace('!=','==')
    elif '<' in row:
        row=row.replace('<','>=')
    elif '>' in row:
        row=row.replace('>','<=')
    return row
# Calling frama-C for all asserts and path condition and finally calling getconds.py
def generate(a_dir):
    eachfile = get_files(a_dir+'/singlepaths','path*.c')
    iffile =get_files(a_dir+'/singlepaths','ifpath*.c')
    print 'Running Frama-C WP-Plugin.......'
    cmd = "frama-c -wp -wp-timeout 50 -wp-model 'hoare' -wp-simpl "+a_dir+"/singlepaths/" + iffile[0] +" -wp-out "+a_dir+"/singlepaths/"+iffile[0].replace('.c','')
    print cmd
    try:
        out =subprocess.check_output(cmd,shell=True,stderr=subprocess.STDOUT)
        print out
    except subprocess.CalledProcessError as e:
        print e.output
        raise RuntimeError("command '{}' \n return with error (code {}):\n {}".format(e.cmd, e.returncode, e.output))
        exit(1)
    
    cmd = "frama-c -wp -wp-timeout 50 -wp-model 'Hoare' -wp-simpl "+a_dir+"/singlepaths/" + eachfile[0] +" -wp-out "+a_dir+"/singlepaths/"+eachfile[0].replace('.c','')
    print cmd
    try:
        out =subprocess.check_output(cmd,shell=True,stderr=subprocess.STDOUT)
        print out
    except subprocess.CalledProcessError as e:
        print e.output
        raise RuntimeError("command '{}' \n return with error (code {}):\n {}".format(e.cmd, e.returncode, e.output))
        exit(1)
    os.chdir(a_dir)
    cmd = a_dir+"/./getconds.py"
    print cmd
    try:
        out =subprocess.check_output(cmd,shell=True,stderr=subprocess.STDOUT)
        print out
        final_prob_f = open('pathprobs.txt','r')
        pathprobs=final_prob_f.readlines()
        final_prob_f.close()
        print "Failure probability values for "+pathprobs[-1]
#        final_prob=0
#        for each_prob in pathprobs:
#            print each_prob
#            final_prob+=float(each_prob.split(':')[1])
#        print "*******************************************************************"
#        print "Failure Probability of program is "+`final_prob`        
#        print "*******************************************************************"
    except subprocess.CalledProcessError as e:
        print e.output
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        exit(1)

# Paths are generated for path probability computation, Frama-C is called for one path till final assertion, calls getconds.py
# to generate the probability value.
def main(argv):
    a_dir = os.getcwd(); #a_dir <- current directory
    cfile_name =  get_files(a_dir+'/singlepaths','singlepath*.c') # c_file_name[0] <- one path generated from wpcond_paths.cpp 
    if(len(cfile_name)>0): 
        cfile = open(a_dir+'/singlepaths/'+cfile_name[0],'r') # This will only happen if there is no unrolling, singlepaths will contain one path starts with singlepath 
    else:
        cfile = open(a_dir+'/temp.c','r') #If unrolling is done, the current path is stored in temp.c
    rows= cfile.readlines() #rows <- all lines from the path
    cfile.close()
    totalasserts=0
    totalifs=0
    totalinvs=[]
    subinvs=[]    
    # If no path number is provided as an argument    
    try:
        pathno=int(argv[0]) 
    except:
        pathno=0 

# If the assert contains 'IF/LOOP' change the assert to 'IF', if it contains 'assert' make it assert not in Frama-C format 
    for i in range(len(rows)):
        if 'assert' in rows[i]:
            if 'IF' in rows[i] or 'LOOP' in rows[i]:
                rows[i]=rows[i].replace(rows[i].split(':')[0]+':','if') 
                totalifs+=1
                totalasserts+=1
            else:
                rows[i]=rows[i].replace(rows[i].split(':')[0]+':','assert')
                totalasserts+=1 #Counting the total number of asserts
        elif 'invariant' in rows[i]:
            subinvs.append(i)
            if not 'invariant' in rows[i+1]:
                totalinvs.append(subinvs)
                subinvs=[]
            totalinvs+=1
    
      
    ifs=1 #Final if naming as ACTUAL
    
    cfileinif = open(a_dir+'/singlepaths/ifpath'+`pathno`+'.c','w')
    for row in rows:
        if 'if' in row:
            if ifs!=totalifs:
                row = row.replace('if','//@ assert IF'+`ifs`+' : ')
                cfileinif.write(row)
            else:
                row = row.replace('if','//@ assert ACTUAL :')
                cfileinif.write(row)
            ifs+=1
        elif 'assert' in row:
            pass
        elif '//#' in row:
            pass
        else:
            cfileinif.write(row)
    cfileinif.close()    
    
    
    # This part computes the failure probabilities of the asserts in a path
    olds=1
    probs='' # Test reliability data for each assert
    txtfile = open(a_dir+'/singlepaths/path'+`pathno`+'_assert'+`totalasserts`+'.txt','w') #contains the test reliability data for the current assert
    
    cfileint = open(a_dir+'/singlepaths/path'+`pathno`+'_assert'+`totalasserts`+'_t.c','w') #considering current assert as true
    for row in rows:
        if 'assert' in row or 'if' in row:
            if(olds<totalasserts):
                row=row.replace('assert','//@ assert OLD'+`olds`+' : ').replace('if','//@ assert OLD'+`olds`+' : ') # Naming the previous asserts as assert old and num
                cfileint.write(row)
            elif(olds==totalasserts):
                row=row.replace('assert','//@ assert ACTUAL :').replace('if','//@ assert ACTUAL :') 
                cfileint.write(row)
                row = invert(row)
                #Probabilities are written as P4+P3-P2-P1. Only the test reliability value of current assert will be separated by '+' 
                probs=probs.replace('-','+',2).replace('+','',1)
                txtfile.write(probs)
                txtfile.close()
            else:
                cfileint.write(row)
            olds+=1
        elif '//#' in row: #Reading test reliability data
            if olds<= totalasserts:
                probs='-'+row.replace('//#','').strip()+probs
            else:
                pass
        else:
            cfileint.write(row)
    cfileint.close()
        
    generate(a_dir)
    
    #handling whiles with invarinats
    lineslist=[]
    try:
        read_n_invs=open(a_dir+'/invariants.txt','r')
        lineslist=read_n_invs.readlines()
        read_n_invs.close()
    except:
        pass
    countinvs=-1
    olds=1
    rowid=-1
    for inv in range(len(totalinvs)):
        inv_t = open(a_dir+'/singlepaths/inv_t.c','w')
        inv_f = open(a_dir+'/singlepaths/inv_f.c','w')
        probtxt = open(a_dir+'/singlepaths/inv.txt','w')
        probs=''
        for row in rows:
            rowid+=1
            if 'assert' in row or 'if' in row:
                if(countinvs<inv):
                    row=row.replace('assert','//@ assert OLD'+`olds`+' : ').replace('if','//@ assert OLD'+`olds`+' : ') 
                    inv_t.write(row)
                    inv_f.write(row)
                elif(countinvs==inv and 'assert' in row):
                    row=row.replace('assert','//@ assert ACTUAL :')
                    inv_t.write(row)
                    row=invert(row)
                    inv_f.write(row)
                else:
                    inv_t.write(row)
                    inv_f.write(row)
            elif '//#' in row:
                if countinvs<=inv:
                    probs='-'+row.replace('//#','').strip()+probs
                else:
                    pass
            elif 'invariant' in row:
                if not 'invariant' in rows[rowid+1]:
                    countinvs+=1
                if countinvs<=inv:
                    inv_t.write(row)
                    if countinvs==inv:
                        
                        if len(lineslist[countinvs])>0:
                            conds=lineslist[countinvs].split('->')
                            for cond in conds:
                                inv_f.write('//@ loop invariant '+cond+';')
            else:
                inv_t.write(row)
                inv_f.write(row)
        probs=probs.replace('-','+',2).replace('+','',1)
        probtxt.write(probs)
        probtxt.close()
        inv_t.close()
        inv_f.close()
        toggle =False
        for eachline in lineslist:
            if len(eachline)>0:
                toggle=True
                break
        if toggle:
            cmd = a_dir+"/./getconds.py inv_t.c inv_f.c"
        else:
            cmd = a_dir+"/./getconds.py inv_t.c"
        print cmd
        try:
            out =subprocess.check_output(cmd,shell=True,stderr=subprocess.STDOUT)
            print out
            final_prob_f = open('pathprobs.txt','r')
            pathprobs=final_prob_f.readlines()
            final_prob_f.close()
            print "Failure probability values for "+pathprobs[-1]
        except subprocess.CalledProcessError as e:
            print e.output
            raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
            exit(1)
    return

# Starts Here
if __name__ == "__main__":
   main(sys.argv[1:]) #Read the path number for naming convention of the files
