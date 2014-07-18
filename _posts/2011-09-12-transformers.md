---
layout: post
category : blog
tagline: "."
tags : [blog haskell language haskelltricks]
e: Rose tree transformer
---


This will get expanded later, but until then, if any one is looking for a transformer instance for a rose tree,

~~~
data Tree m = Node { getm :: m, getl :: [Tree m] } deriving (Show, Eq)

data TreeT m a = TreeT (m (Tree a))
runTreeT (TreeT m) = m
instance Monad m => Monad (TreeT m) where
       return m = TreeT $ return $ Node m []
       tmb_v >>= f = TreeT $ runTreeT tmb_v >>= onone f
               where onone f (Node b_ex b_ets) = do
                                 Node ex ets <- runTreeT (f b_ex)
                                 ets_ <- mapM (onone f) b_ets
                                 return $ Node ex (ets_ ++ ets)

instance MonadTrans TreeT where
      lift x = TreeT $ x >>= return . (flip Node [])
~~~

And another monad transformer for a tree with data  only in leaves

~~~
data Tree_ c = Node_ { getl_ :: [Tree_ c] }
                       | Leaf_ { getc_ :: c} deriving (Show, Eq)
data Tree_T m a = Tree_T (m (Tree_ a))
runTree_T (Tree_T m) = m

instance Monad m => Monad (Tree_T m) where
       return m = Tree_T $ return $ Leaf_ m
       tmb_v >>= f = Tree_T $ runTree_T tmb_v >>= onone f
                 where onone f (Node_ b_ets) = do
                                  ets_ <- mapM (onone f) b_ets
                                  return $ Node_ ets_
                            onone f (Leaf_ x) = runTree_T $ f x

instance MonadTrans Tree_T where
          lift x = Tree_T $ x >>= return . Leaf_
~~~

