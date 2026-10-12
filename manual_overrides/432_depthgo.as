public function depthgo() : void
{
   var someArray:Array = null;
   var i:* = undefined;
   setChildIndex(this.skitback,numChildren - 1);
   someArray = new Array(this.char1,this.char2,this.char3,this.char4,this.char5,this.char6,this.char7,this.char8,this.prop1,this.prop2,this.prop3,this.prop4,this.prop5,this.prop6,this.prop7,this.prop8,this.prop9,this.prop10);
   someArray.sortOn("y",Array.ASCENDING);
   for(i in someArray)
   {
      setChildIndex(someArray[i],numChildren - 1);
   }
   setChildIndex(this.groundtouch,numChildren - 1);
   setChildIndex(this.topscene,numChildren - 1);
   setChildIndex(this.botx,numChildren - 1);
   setChildIndex(this.propsgo,numChildren - 1);
   setChildIndex(this.posesgo,numChildren - 1);
   setChildIndex(this.editmodego,numChildren - 1);
   setChildIndex(this.chatscenego,numChildren - 1);
   setChildIndex(this.bgscenego,numChildren - 1);
   setChildIndex(this.savesgo,numChildren - 1);
   setChildIndex(this.fakefadex,numChildren - 1);
   setChildIndex(this.scenehider,numChildren - 1);
   setChildIndex(this.topblack,numChildren - 1);
}
