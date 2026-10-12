public static function setTextField(textField:flash.text.TextField) : *
{
   if(!textField.parent)
   {
      return;
   }
   p.textField = textField;
   var clickSprite:flash.display.Sprite = new flash.display.Sprite();
   with(clickSprite.graphics)
   {
      beginFill(0,0);
      moveTo(0,0);
      lineTo(textField.width,0);
      lineTo(textField.width,textField.height);
      lineTo(0,textField.height);
      endFill();
   }
   clickSprite.name = textField.name + "_clickSprite";
   clickSprite.x = textField.x;
   clickSprite.y = textField.y;
   textField.parent.addChildAt(clickSprite,textField.parent.getChildIndex(textField));
}
