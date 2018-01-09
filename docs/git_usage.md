# Git Usage
旨在说明如何通过git实现代码编写的多方协作以及同步，将以项目rebuild为例进行说明

## 第一步，代码fork
打开[老王的rebuild项目](http://192.168.1.107/Vanderick/rebuild)，点击fork拷贝到自己的代码区，此时在自己的gitlab账户下应当有了对应的仓库，以用于Saint longlive为例，此时对应的项目地址为[sll-rebuild](http://192.168.1.107/sll/rebuild#new-crawler-system)
tips：由于没有对应的权限，不同的用户打开将是404

## 第二步，建立本地仓库
这一步，是从自己的仓库中拉项目到本地，以sll为例：
```
git clone http://116.231.250.63:81/sll/rebuild.git
```
此时，你的本地代码库和远程的托管仓库对应起来了，看一看
```
git remote -v
```
然后显示：
```
origin	http://116.231.250.63:81/sll/docs.git (fetch)
origin	http://116.231.250.63:81/sll/docs.git (push)
```
你以为我婆婆妈妈说了这么多是不是啰嗦，到时候要是看不明白可不要回过来问我。然后我们添加上游仓库，即老王的远程仓库
```
git remote add upstream http://116.231.250.63:81/Vanderick/rebuild.git
```
此时再次：
```
git remote -v
```
显示一下表示成功：
```
origin http://116.231.250.63:81/sll/rebuild.git (fetch)
origin http://116.231.250.63:81/sll/rebuild.git (push)
upstream http://116.231.250.63:81/Vanderick/rebuild.git (fetch)
upstream http://116.231.250.63:81/Vanderick/rebuild.git (push)
```

## 第三步，时刻保持与老王的rebuild项目的同步
在做任何操作前，尤其是准备修改前，一定要时刻保持与老王的项目（也就是你fork的来源）的同步。
接下来操作四连发.
#### 从老王的仓库fetch内容存储到本地分支upstream/master
```
git fetch upstream
```
然后执行以下命令查看结果
```
git branch -a
> * master
  remotes/origin/HEAD -> origin/master
  remotes/origin/master
  remotes/upstream/master （这个是老王的master分支）
```
看到upstream/master了吗，这个就表示从老王的仓库拉过来的。
#### 然后把老王仓库拉到本地的内容合并到自己的仓库里面
```
git merge upstream/master
```
#### 更新sll同学的远程仓库
```
git checkout master
git push origin master
```
##### 此时，sll同学本地的仓库，远程的仓库，都与老王的远程仓库保持一致了

## 第四步，提交修改至远程仓库
比如sll同学对parse/detail/csn_detail.csv进行了修改，执行以下命令查看当前编辑状态
```
git status
> modified: parse/detail/csn_detail.csv
```
然后使用以下命令add所有修改到本地仓库：
```
git add .
git commit -m "调整csn平台的文章解析规则"
```
最后执行以下操作，将修改提交到远程仓库
```
git push origin master
```

## 第五步，提交pr到项目的拥有者--老王
- 点击Projects->rebuild->Files,打开项目所在的[master分支](http://192.168.1.107/sll/rebuild/tree/master)
- 点击Merge Requests，选择 New Merge Requests
- 一般Source branch 选择 sll/rebuild master， Target branch选择默认
- 点选Compare brances and contine
- 描述里面主要填写好title以及description然后点底下的提交按键，完事儿~
- 接下来，直接喊老王进行code review && accept Requests就OK咯

## tips：
so easy 对吧：

![](http://img2.biaoqingjia.com/biaoqing/201608/687e2d9130e76d39ca5d39136d1f91bb.gif)
