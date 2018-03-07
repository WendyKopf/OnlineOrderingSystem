#Practice for working in Python

#reversing an integer, takes an integer and returns the reverse of said integer
def reverseInt(n):
	a = 0
	while n>0 :
		temp1 = n % 10
		n = n/10
		if temp1 > 0 :  
			a = (a*10 + temp1)
	return a
	
#Another function to practive with is to detect a prime number

def isPrime (n):
	if n > 1:
		for i in range (2, n):
			if (n % i) == 0:
				return False
		else:
			return True
	else: 
		return False
#Just a practice line command- for creating a list of primes in the range of 100

def makeListofPrimes(n):
	l = []
	for x in range(n+1): #adjust the n to n+1 to include the last element
		if isPrime(x):
			l.append(x)
	return l


