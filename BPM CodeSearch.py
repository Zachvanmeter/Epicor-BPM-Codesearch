from os import path, makedirs
from sys import exit
from tkinter import *

import pyodbc


# pyinstaller -F --icon="TMF Epicor.ico" "BPM CodeSearch.py"

# ######################################### #
#############################################
# ######################################### #

		# KNOBS TO TURN / SETTINGS #
			
REPLACEDICT = \
{		# because apparently I dont know how to use .decode()
	'&#x0A;':'\n'
	,'&amp;':'&'
	,'&quot;':'"'
	,'&#x0D;':''
	,'&#x09;':'\t'
	,'&gt;':'>'
	,'&lt;':'<'
	,'&le;':'≤'
	,'&ge;':'≥'
}

# ######################################### #
#############################################
# ######################################### #

def GenBPMCode(Server,Database,q1,q2,NotClause,IgnrComt,Output,ShowCode,IndexEnable,IncludeBase):
	def IsOkay(IndexEnable,IsEnabled):	
		if IndexEnable == 0 :
			if not IsEnabled:
				return False
			else:
				return True
		elif IndexEnable == 1:
			return True
		elif IndexEnable == 2:
			if not IsEnabled:
				return True
			else:
				return False
	def IsBase(IncludeBase,Name,DirectiveType):
		if IncludeBase == 0:
			if 'BASE' in Name or DirectiveType == 'OutOfTrans':
				return False
			else:
				return True
		elif IncludeBase == 1:
			return True
		elif IncludeBase == 2:
			if 'BASE' in Name or DirectiveType == 'OutOfTrans':
				return True
			else:
				return False
	def CleanBody(Body):
		Body = Body.encode('latin1', errors='ignore').decode('unicode_escape', errors='ignore')
		for k,v in REPLACEDICT.items():
			Body = Body.replace(k,v)
		return Body
	def CleanLine(line):
		while line[0] == ' ' or line[0] == '\t':
			line = line[1:]
		return line
	def PrintMatchingLines(q1,IgnrComt,BpmCount,lines):
		p = 0
		if not q1 == '':
			for i, line in enumerate(lines):
			
				if not IgnrComt: 
					Goodline = line.split('//')[0]
				else:
					Goodline = line
					
				if q1.upper() in Goodline.upper():
					print('Line:'+str(i+1)+' | '+CleanLine(line))
					p = 1
				elif q1.upper() in line.upper():
					p = 2
					
			if p == 0:	print('Search Clause exists in Widget')
			if p == 1:	pass # prints the line as above
			if p == 2:	print('Search Clause exists in Comment')
	def GenCustomCode(Body):
		head,sep,tail = Body.partition('" Code="')
		Code,sep,tail = tail.partition('" ExecutionRule="')
		return Code
	def FileHandler(BpMethodCode,Body):
		Filename = 'BPMs/'+BpMethodCode+'.txt'	
		filepath,sep,name = Filename.rpartition('/')
		if not path.isdir(filepath):
			makedirs(filepath+'/')
		with open(Filename, 'w') as f:
			f.write(Body)
	def FindQ(q1,q2,NotClause,Body):
		if q2 != '':
			qFound = (q1.upper() in Body.upper() and (NotClause == (q2.upper() in Body.upper())))
		else:
			qFound = (q1.upper() in Body.upper())
		return qFound	
	# ###################################### #
	conn = pyodbc.connect('Driver={SQL Server};'
						  'Server='+Server+';'
						  'Database='+Database+';'
						  'Trusted_Connection=yes;')
	cursor = conn.cursor()
	cursor.execute(('SELECT '
		+'         BpDirective.BpMethodCode, '
		+'         BpDirectiveType.Name, '
		+'         BpDirective.Name, '
		+'         BpDirective.Body, '
		+'         BpDirective.IsEnabled '
		+'FROM     <DatabaseName>.Ice.BpDirective as BpDirective '
		+'INNER JOIN '
		+'         <DatabaseName>.Ice.BpDirectiveType as BpDirectiveType '
		+'      ON BpDirectiveType.Source = BpDirective.Source '
		+'     AND BpDirectiveType.DirectiveType = BpDirective.DirectiveType '
		).replace('<DatabaseName>',Database))
	print('Generating BPM Output...\n')
	BpmCount = 0 
	BpmTotal = 0

	for row in cursor:
		BpMethodCode,DirectiveType,Name,Body,IsEnabled = row
		Okay = IsOkay(IndexEnable,IsEnabled)
		Base = IsBase(IncludeBase,Name,DirectiveType)
	
		if Body and Okay and Base:
			BpmTotal += 1
			Body = CleanBody(Body)
			Code = GenCustomCode(Body)
			
			Header = '\n########################\n\n'+DirectiveType+' # '+BpMethodCode+' '+Name
			Detail = '\t\t\tEnabled\n' if IsEnabled else '\t\t\tDisabled\n'
			Footer = '\n########################\n\n'
			
			
			if FindQ(q1,q2,NotClause,Body):
				print(Header)
				print(Detail)
				if ShowCode == 0: PrintMatchingLines(q1,IgnrComt,BpmCount,Code.split('\n'))
				if ShowCode == 1: print(Code)
				if ShowCode == 2: print(Body)
				print(Footer)
				BpmCount += 1
			elif q1.upper() in Name.upper():
				print(Header+'\n'+Detail+'\nSearch Clause exists in BPM Name\n'+Footer)
				BpmCount += 1
			if Output == 1: FileHandler(BpMethodCode,Body)
	
	print('\nSearch Complete for "%s". %s/%s BPMs Displayed'%(q1,BpmCount,BpmTotal))

class SQLSearchTool:
	def __init__(self,master):
		self.master = master
		#self.width  = master.winfo_screenwidth()
		#self.height = master.winfo_screenheight()-50
		w,h = 550,225
		master.geometry('%dx%d'%(w,h))
		
		self.BF = ('Consolas 10')
		self.bg = Canvas(master, width=w,height=h)
		self.bg.place(x=10,y=10)
		
		self.DeclareVars()
		self.BuildFrame()
		
	def DeclareVars(self):
		self.Buttons = {}
		self.Output = IntVar()
		self.IndexEnable = IntVar()
		self.ShowCode = IntVar()
		self.IncludeBase = IntVar()
		self.IgnrComt = IntVar()
		self.NotClause = IntVar()
		
		self.q1 = StringVar()
		self.q2 = StringVar()
		self.q1.set('')
		self.q2.set('')
		self.Database = StringVar()
		self.Database.set('EpicorERP')
		self.Server = StringVar()
		self.Server.set('TMFSVR10')
		
		
		self.Output.set(0)		    # 1
		self.IndexEnable.set(0)		# 1,2
		self.ShowCode.set(0)		# 1,2,3
		self.IncludeBase.set(0)		# 1,2
		self.IgnrComt.set(0)		# 1
		self.NotClause.set(0)		# 1
		
	def BuildFrame(self):
		def UpdateNot():
			if   self.NotClause.get() == 0:
				self.NotChk.config(text=r'& ')
			elif self.NotClause.get() == 1:
				self.NotChk.config(text=r'&!')
			self.bg.update()
			self.master.after(100,UpdateNot)
		# ############################# #
			# Output Line type
		self.ShowCCan = Canvas(self.bg, width=100,height=500)
		self.master.bind("<Return>", self.SearchWrapper)
		self.ShowCCan.place(x=10,y=10)
		Label(self.ShowCCan, text='Output Content', anchor=W).pack(fill=X)
		Radiobutton(self.ShowCCan, font=self.BF, text='Lines         ', variable=self.ShowCode, value=0).pack()
		Radiobutton(self.ShowCCan, font=self.BF, text='Custom Code   ', variable=self.ShowCode, value=1).pack()
		Radiobutton(self.ShowCCan, font=self.BF, text='Entire BPM    ', variable=self.ShowCode, value=2).pack()
		Radiobutton(self.ShowCCan, font=self.BF, text='Name          ', variable=self.ShowCode, value=3).pack()
		Checkbutton(self.ShowCCan, font=self.BF, text='Write to File ', variable=self.Output).pack()
		Checkbutton(self.ShowCCan, font=self.BF, text='Yield Comments',variable=self.IgnrComt).pack()
		
		
			# BPM Filters
		self.FiltrCanvas = Canvas(self.bg, bg='Gray75', width=350,height=105)
		self.FiltrCanvas.place(x=150,y=50)
		self.InBseCan = Canvas(self.FiltrCanvas, width=100,height=500)
		self.InBseCan.place(x=5,y=5)
		Label(self.InBseCan, text='BPM Filters', anchor=W).pack(fill=X)
		Radiobutton(self.InBseCan, font=self.BF, text='Custom BPMs         ', variable=self.IncludeBase, value=0).pack()
		Radiobutton(self.InBseCan, font=self.BF, text='Custom and Base BPMs', variable=self.IncludeBase, value=1).pack()
		Radiobutton(self.InBseCan, font=self.BF, text='Base BPMs           ', variable=self.IncludeBase, value=2).pack()
		self.NAbleCan = Canvas(self.FiltrCanvas, width=100,height=500)
		self.NAbleCan.place(x=175,y=5)
		Label(self.NAbleCan, text='', anchor=W).pack(fill=X)
		Radiobutton(self.NAbleCan, font=self.BF, text='Enabled             ', variable=self.IndexEnable, value=0).pack()
		Radiobutton(self.NAbleCan, font=self.BF, text='Enabled and Disabled', variable=self.IndexEnable, value=1).pack()
		Radiobutton(self.NAbleCan, font=self.BF, text='Disabled            ', variable=self.IndexEnable, value=2).pack()
		
		Label(self.bg, text='Server', anchor=W).place(x=160,y=8)
		Entry(self.bg, font=self.BF,  width=12, textvariable=self.Server).place(x=200,y=10)
		Label(self.bg, text='Database', anchor=W).place(x=290,y=8)
		Entry(self.bg, font=self.BF,  width=18, textvariable=self.Database).place(x=345,y=10)
        
		
		
		Entry(self.bg, font=self.BF,  width=12, textvariable=self.q1).place(x=200,y=170)
		self.NotChk = Checkbutton(self.bg,  font=self.BF, variable=self.NotClause)
		self.NotChk.place(x=310,y=165)
		Entry(self.bg, font=self.BF,  width=12, textvariable=self.q2).place(x=360,y=170)
		Button(self.bg,font=self.BF,  text='Search', command=self.SearchWrapper).place(x=455,y=165)
		
		UpdateNot()
		
	def SearchWrapper(self, Event=None):
		Server = self.Server.get()
		Database = self.Database.get()
		q1 = self.q1.get()
		q2 = self.q2.get()
		NotClause = True if self.NotClause.get() == 0 else False
		IgnrComt = False if self.IgnrComt.get() == 0 else True
		Output = self.Output.get()
		ShowCode = self.ShowCode.get()
		IndexEnable = self.IndexEnable.get()
		IncludeBase = self.IncludeBase.get()
		#print(Database,q1,q2,NotClause,Output,ShowCode,IndexEnable,IncludeBase)
		GenBPMCode(Server,Database,q1,q2,NotClause,IgnrComt,Output,ShowCode,IndexEnable,IncludeBase)
		
def RunUI():
	root = Tk()
	root.title('SQL Search Tool')
	app = SQLSearchTool(root)
	root.mainloop()
	
			
		## TODO ##
	
	# make button for each result with built in output textbox
			
	# ignore case option
	
	# ignore widgets option
	
	# show n lines before and after
	
def Main():
	while True:
		q1 = input('Enter BPM Search Clause: ')
		print()
		print('Press Enter to Continue or...')
		print('  1 to write the contents of all BPMs to subdirectory: ')
		Output = input()
		if Output == '1':
			Output = int(Output)
		else:
			Output = 0#1
		
		
		
		print('Press Enter to Index Enabled BPMs or...')
		print('  1 to index both Enabled and Disabled BPMs: ')
		print('  2 to index only Disabled BPMs: ')
		IndexEnable = input()
		if IndexEnable == '1' or IndexEnable == '2':
			IndexEnable = int(IndexEnable)
		else:
			IndexEnable = 0#1,2
		
		
		print('Press Enter to Index matching BPM Lines or...')
		print('  1 to return matching BPM Custom code')
		print('  2 to return matching BPM in its Entirity')
		print('  3 to return matching BPM names')
		ShowCode = input()
		if ShowCode == '1' or ShowCode == '2' or ShowCode == '3':  
			ShowCode = int(ShowCode)
		else:
			ShowCode = 0#1,2,3
		
		
		print('Press Enter to Search Only Custom BPMs or...')
		print('  1 to index Custom and Base BPMs')
		print('  2 to index Base BPMs only')
		IncludeBase = input()
		if IncludeBase == '1' or IncludeBase == '2':
			IncludeBase = int(IncludeBase)
		else:
			IncludeBase = 0#1,2
		
		#GenBPMCode(q1,Output,ShowCode,IndexEnable,IncludeBase)

if __name__ == '__main__':
	RunUI()
	#Main()
	
		