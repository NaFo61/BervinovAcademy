# print("hello", end=', ')
# print("margo")

# a = 5
# b = 10
# if a > b:
#     print("dog")
# elif a > b:
#     print("cat")
# elif a > 2:
#     print("fish")
# else:
#     print("bird")

# num = int(input())
# print(num % 2 == 1)

# a = 5
# b = 10
# print(a + b)
# print(a - b)
# print(a * b)
# print(a / b)
# print(a % b)
# print(a ** b)
# print(a // b)
# print(36 ** 0.5)
# print(13 // 10)
# print(-13 // 10)

# print(3 ** 1 ** 2)


# s = 'О Мирослав помоги мне'
# print(s[0])
# print(s[5])
# print(s[-1])
# print(s[0:5])
# print(s[0:5:2])


# s = 'о КаК же ТЫ МОГЛА не влюбиться в меня?'
# print(s.upper())
# print(s.lower())
# print(s.capitalize())
# print(s.title())
# print(s.replace(' ', '_'))
# print(s.split())


s = 'о КаК же ТЫ МОГЛА не влюбиться в меня?'

# for i in s:
#     print(i)

# for i in range(len(s)):
#     print(i, s[i])


# l = len(s)
# while l > 0:
#     print(s[l - 1])
#     l -= 1


s = input()
s = s[::-1]  # развернуть строку
for i in s:
    print(i)    
