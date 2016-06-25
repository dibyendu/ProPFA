/* Input: Output.txt which contains the output of invgen 
*Task of the program: Extract the loop invariants from the output file of invgen
*                     Convert the loop invariants in to frama-c format
*                     Calls invariant script which inserts the loop invariant before the while loop
* Output: invariant.txt from which the invariants are inserted into the frama_c_input.c file
*/
/******************************************************************************************************************************/
#include <iostream>
#include <fstream>
#include <algorithm>
#include<bits/stdc++.h>
using namespace std;
string trim(string const& str)       /*Get the loop invariants from the file generated by invgen*/
{
 int first=0,last=str.length()-1;
  	while(str[first]!='[')
  	{
  		first++;
		
  	}
	first++;
	while(str[last]==' ' || str[last]=='\t'|| str[last]==']' ) 
  	{
  		last--;
 	}
    return str.substr(first, last-first+1);
}
string trim2(string str)                           /*invgen generates invariant in the format =>/=< and frama-c accepts the opposite
							This function converts invariants in frama-c format*/
{
	int i=0, last=str.length();
	char tmp;
	while(str[i]!='=')
	{
		i++;
	}
	tmp=str[i];
	str[i]=str[i+1];
	str[i+1]=tmp;
	return str;
}
	
int main(void)
{
	int i=0;
	string line,line2;
	//string str2="//@ loop invariant ";
	string str=" && ";
	system("sed -n -e '/#Invariant:/,$p' output.txt > invariant_val.txt");
	system("sed '1d' invariant_val.txt > tmpfile"); 
	system("mv tmpfile invariant_val.txt");
	ifstream inFile;
	inFile.open("invariant_val.txt");
	getline(inFile,line);
	line2=trim(line);
	inFile.close();
	ofstream outFile;
	outFile.open("invariant_val.txt");
	replace(line2.begin(),line2.end(),',','\n');
	outFile << line2 << endl;
	outFile.close();
	ofstream outfile;
	outfile.open("tmp.txt");
	ifstream infile;
	infile.open("invariant_val.txt");
	getline(infile,line);
	line2=trim2(line);

	//line2.insert(0,str2);
	outfile << line2;
	while(getline(infile,line))
	{
		line2=trim2(line);
		//line2.insert(0,str);
		
		outfile << " -> " << line2;
	}
	outfile <<" ;";
	infile.close();
	outfile.close();
	system("mv tmp.txt invariant.txt");
	system("rm output.txt");
	return 0;
}
	
